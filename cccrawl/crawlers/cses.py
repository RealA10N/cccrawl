import html
from collections.abc import AsyncIterable
from datetime import datetime, timezone
from io import StringIO
from logging import getLogger
from typing import NamedTuple

import backoff
import bs4
from bs4 import BeautifulSoup
from httpx import HTTPError, Response
from limited import AsyncLimiter
from pydantic import AwareDatetime, HttpUrl, computed_field

from cccrawl.crawlers.base import Crawler
from cccrawl.crawlers.error import CrawlerError
from cccrawl.crawlers.toolkit import CrawlerToolkit
from cccrawl.files.base import FileUploadError
from cccrawl.integrations.cses import CsesIntegration
from cccrawl.models.base import ModelId
from cccrawl.models.problem import Problem
from cccrawl.models.submission import CrawledSubmission, Submission, SubmissionVerdict

logger = getLogger(__name__)

cses_limiter = AsyncLimiter(limit=3, every=5)
backoff_on_exception = backoff.on_exception(backoff.expo, HTTPError, max_time=120)


class CsesCredentials(NamedTuple):
    """Representing credentials of a CSES user, that is used by the crawler
    for crawling accepted submissions."""

    username: str
    password: str


class HackableSubmissionDescriptor(NamedTuple):
    """Representing a single hackable submission from hacking page of a CSES
    problem."""

    submission_username: str
    submission_url: HttpUrl


class CsesCrawledSubmission(CrawledSubmission[CsesIntegration]):
    """A dataclass containing crawled information about submissions from
    https://cses.fi.
    Since submissions are crawled by looking at the statistics page of the user
    (for example, https://cses.fi/problemset/user/89310/), the initial crawled
    data is minimal. In particular, we do not have access to 'trivial' metadata
    like the submission time, and CCCrawler can only detect at most 2 submission
    per problem (one accepted and one rejected)."""

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> ModelId:
        return ModelId(
            self._hash_tokens(
                self.integration,
                self.problem,
                self.verdict,
            )
        )


class CsesSubmission(Submission[CsesIntegration], CsesCrawledSubmission):
    pass


class CsesCrawler(Crawler[CsesIntegration, CsesCrawledSubmission, CsesSubmission]):
    def __init__(
        self,
        toolkit: CrawlerToolkit,
        credentials: CsesCredentials | None = None,
    ) -> None:
        super().__init__(toolkit)

        self._credentials = credentials
        if not self._credentials:
            logger.warning(
                "Credentials not provided for CSES crawler, functionality limited"
            )

    async def load(self) -> None:
        if self._credentials:
            await self._preform_session_login(self._credentials)

    @property
    def submission_model(self) -> type[CsesSubmission]:
        return CsesSubmission

    async def crawl(
        self, integration: CsesIntegration
    ) -> AsyncIterable[CsesCrawledSubmission]:
        if (user_number := integration.user_number) is None:
            logger.info("No available CSES user, skipping.")
            return

        response = await self._get_user_profile(user_number)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        table = soup.find("table")
        if table is None:
            raise CrawlerError(f"CSES user {user_number} does not exist")

        submitted_tags = table.find_all("a", {"class": {"full", "zero"}})

        for a_tag in submitted_tags:
            yield CsesCrawledSubmission(
                integration=integration,
                problem=Problem(problem_url="https://cses.fi" + a_tag["href"][:-1]),
                verdict=SubmissionVerdict.accepted
                if "full" in a_tag["class"]
                else SubmissionVerdict.rejected,
            )

    async def finalize_new_submission(
        self, crawled_submission: CsesCrawledSubmission
    ) -> CsesSubmission:
        """Finalize a crawled CSES submission.
        This is done by searching for the submission on the hacking list."""

        if crawled_submission.verdict == SubmissionVerdict.rejected:
            # The submission won't appear on the hacking list, since it is not
            # accepted.
            return CsesSubmission.from_crawled(crawled_submission)

        async for hackable_submission in self._get_hackable_submissions(
            crawled_submission.problem
        ):
            if (
                hackable_submission.submission_username.casefold()
                == crawled_submission.integration.handle.casefold()
            ):
                return await self._finalize_submission_from_hackpage(
                    crawled_submission,
                    hackable_submission,
                )

        # If for some reason the submission wasn't found in the recent
        # submissions list, build submission from existing data only.
        logger.info(
            f"CSES Submission {crawled_submission.id} not found in hacking list."
        )
        return CsesSubmission.from_crawled(crawled_submission)

    async def _get_hackable_submissions(
        self, problem: Problem
    ) -> AsyncIterable[HackableSubmissionDescriptor]:
        if not self._credentials:
            return  # credentials are required

        response = await self._get_list_of_hackable_submissions_page(problem)
        content = self._get_cses_page_content(response)

        table = content.find("table")
        if not isinstance(table, bs4.Tag):
            # Table not found if user not logged in (invalid credentials),
            # or the user did not solve the problem. In both cases we 'fail'
            # quietly, as if there are no submissions to the problem
            if not self._check_if_logged_in(response):
                logger.warning(
                    "CSES Credentials provided, but crawling session is logged out. "
                    "Credentials may be invalid OR sessions expired for some reason."
                )
            return

        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if not cols:
                continue  # skip over header row(s)

            submission_user = cols[1].text.strip()
            submission_path = cols[-1].find("a", href=True)["href"]

            yield HackableSubmissionDescriptor(
                submission_username=submission_user,
                submission_url=HttpUrl.build(
                    scheme="https",
                    host="cses.fi",
                    path=submission_path,
                ),
            )

    async def _finalize_submission_from_hackpage(
        self,
        crawled_submission: CsesCrawledSubmission,
        hackable_submission: HackableSubmissionDescriptor,
    ) -> CsesSubmission:
        response = await self._get_hackable_submission_page(hackable_submission)
        content = self._get_cses_page_content(response)
        table = content.find("table")
        if not isinstance(table, bs4.Tag):
            raise CrawlerError("Hacking metadata table not found")

        return CsesSubmission.from_crawled(
            crawled_submission,
            submission_url=hackable_submission.submission_url,
            submitted_at=self._get_submission_time_from_hacking_metadata_table(table),
            raw_code_url=await self._upload_source_code_from_hacking_content(content),
        )

    @staticmethod
    def _check_if_logged_in(response: Response) -> bool:
        soup = BeautifulSoup(response.text)
        return soup.find("a", {"href": "/logout"}) is not None

    async def _preform_session_login(self, credentials: CsesCredentials) -> None:
        csrf_token = await self._get_login_csrf_token()
        await self._post_login_form(csrf_token, credentials)

        # PHP session now should be stored under the PHPSESSID cookie.
        assert "PHPSESSID" in self._toolkit.client.cookies

    @cses_limiter
    @backoff_on_exception
    async def _get_login_csrf_token(self) -> str:
        response = await self._toolkit.client.get("https://cses.fi/login")
        response.raise_for_status()

        csrf_input = BeautifulSoup(response.text, "lxml").find(
            "input", {"name": "csrf_token"}
        )

        if not isinstance(csrf_input, bs4.Tag):
            raise CrawlerError("Can't locate login CSRF token on webpage")

        csrf_token = csrf_input["value"]
        if not isinstance(csrf_token, str):
            raise CrawlerError(f"Unexpected CSRF value {csrf_token}")

        return csrf_token

    @cses_limiter
    @backoff_on_exception
    async def _post_login_form(
        self, csrf_token: str, credentials: CsesCredentials
    ) -> None:
        response = await self._toolkit.client.post(
            "https://cses.fi/login",
            data={
                "csrf_token": csrf_token,
                "nick": credentials.username,
                "pass": credentials.password,
            },
            follow_redirects=False,
        )

        if response.status_code != 302:
            raise CrawlerError(
                f"CSES login failed with status code {response.status_code}.",
                response.text,
            )

    @cses_limiter
    @backoff_on_exception
    async def _get_user_profile(self, user_number: int) -> Response:
        url = f"https://cses.fi/problemset/user/{user_number}/"
        return await self._toolkit.client.get(url)

    @cses_limiter
    @backoff_on_exception
    async def _get_list_of_hackable_submissions_page(
        self, problem: Problem
    ) -> Response:
        problem_url_path = problem.problem_url.path or ""
        _, task_id = problem_url_path.rsplit("/", 1)
        hacking_list_url = f"https://cses.fi/problemset/hack/{task_id}/list/"

        response = await self._toolkit.client.get(hacking_list_url)
        response.raise_for_status()
        return response

    @cses_limiter
    @backoff_on_exception
    async def _get_hackable_submission_page(
        self, submission: HackableSubmissionDescriptor
    ) -> Response:
        hacking_url = str(submission.submission_url)
        response = await self._toolkit.client.get(hacking_url)
        response.raise_for_status()
        return response

    @classmethod
    def _get_cses_page_content(cls, response: Response) -> bs4.Tag:
        soup = BeautifulSoup(response.text, "lxml")
        content = soup.find("div", {"class": "content"})
        if not isinstance(content, bs4.Tag):
            raise CrawlerError("Can't find content tag of hacking page")
        return content

    @classmethod
    def _get_submission_time_from_hacking_metadata_table(
        cls,
        table: bs4.Tag,
    ) -> AwareDatetime:
        date_cell = table.find("td")
        if not isinstance(date_cell, bs4.Tag):
            raise CrawlerError("Hacking metadata table appears to be empty")
        submitted_at = datetime.strptime(date_cell.text, "%Y-%m-%d %H:%M:%S")
        # The datetime is returns in the timezone of the client.
        # we want to convert it to UTC.
        return submitted_at.astimezone(timezone.utc)

    async def _upload_source_code_from_hacking_content(
        self, content: bs4.Tag
    ) -> HttpUrl | None:
        code_block = content.find("pre", {"class": "prettyprint"})
        if not isinstance(code_block, bs4.Tag):
            raise CrawlerError("Submission source code block not found on hacking page")

        code = html.unescape(code_block.text)
        try:
            return await self._toolkit.file_uploader.upload(StringIO(code))
        except FileUploadError:
            logger.warning("Failed to upload submission source code")
            return None
