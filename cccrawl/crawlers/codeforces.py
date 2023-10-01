import html
from collections.abc import AsyncIterable
from datetime import datetime, timezone
from io import StringIO
from logging import getLogger
from typing import Any

import backoff
from bs4 import BeautifulSoup
from httpx import HTTPError, Response
from limited import AsyncLimiter
from pydantic import AwareDatetime, HttpUrl, computed_field

from cccrawl.crawlers.base import Crawler
from cccrawl.crawlers.error import CrawlerError
from cccrawl.files.base import FileUploadError
from cccrawl.integrations.codeforces import CodeforcesIntegration
from cccrawl.models.base import ModelId
from cccrawl.models.problem import Problem
from cccrawl.models.submission import CrawledSubmission, Submission, SubmissionVerdict

logger = getLogger(__name__)


codeforces_api_limits = AsyncLimiter(limit=3, every=3)
codeforces_html_limits = AsyncLimiter(limit=1, every=10)
backoff_on_exception = backoff.on_exception(
    # CODEFORCES is very strict. When getting 403, it takes a while (sometimes
    # a couple of minutes) to return back to normal accepting state! We should
    # avoid getting to the 'blocked' state as much as we can.
    # backoff for: 15, 45, 135, ...
    lambda: backoff.expo(factor=15, base=3),
    HTTPError,
    max_time=600,  # 10m
)


class CodeforcesCrawledSubmission(CrawledSubmission[CodeforcesIntegration]):
    submitted_at: AwareDatetime
    submission_url: HttpUrl

    @computed_field  # type: ignore[misc]
    @property
    def id(self) -> ModelId:
        return ModelId(
            self._hash_tokens(
                self.integration,
                self.problem,
                self.verdict,
                str(self.submitted_at),
                str(self.submission_url),
            )
        )


class CodeforcesSubmission(
    Submission[CodeforcesIntegration], CodeforcesCrawledSubmission
):
    pass


class CodeforcesCrawler(
    Crawler[
        CodeforcesIntegration,
        CodeforcesCrawledSubmission,
        CodeforcesSubmission,
    ]
):
    async def crawl(
        self, integration: CodeforcesIntegration
    ) -> AsyncIterable[CodeforcesCrawledSubmission]:
        if (handle := integration.handle) is None:
            logger.info("No available Codeforces user, skipping.")
            return

        response = await self._get_user_submissions(handle)

        submissions = response.json().get("result", [])
        for sub in submissions:
            yield CodeforcesCrawledSubmission(
                integration=integration,
                problem=Problem(problem_url=self._get_problem_url(sub["problem"])),
                verdict=(
                    SubmissionVerdict.accepted
                    if sub["verdict"] == "OK"
                    else SubmissionVerdict.rejected
                ),
                submitted_at=datetime.fromtimestamp(
                    sub["creationTimeSeconds"], tz=timezone.utc
                ),
                submission_url=self._get_submission_url(submission=sub),
            )

    async def finalize_new_submission(
        self, crawled_submission: CodeforcesCrawledSubmission
    ) -> CodeforcesSubmission:
        response = await self._get_submission_page(crawled_submission.submission_url)
        if response.status_code == 302:
            # Codeforces does not allow to view the submission page for all
            # submissions at any time. For example, submission may be part of a
            # contest that is still running. Submissions to gyms are also not
            # publicly available. We get redirected to home page in that case (302).
            return CodeforcesSubmission.from_crawled(crawled_submission)

        soup = BeautifulSoup(response.text, "lxml")
        code_block = soup.find("pre", id="program-source-text")

        if code_block is None:
            raise CrawlerError(
                "Can't locate source code of submission "
                f"{crawled_submission.submission_url}"
            )

        code = html.unescape(code_block.text)

        try:
            raw_code_url = await self._toolkit.file_uploader.upload(StringIO(code))
        except FileUploadError:
            return CodeforcesSubmission.from_crawled(crawled_submission)

        return CodeforcesSubmission.from_crawled(
            crawled_submission, raw_code_url=raw_code_url
        )

    @codeforces_html_limits
    @backoff_on_exception
    async def _get_submission_page(self, submission_url: HttpUrl) -> Response:
        response = await self._toolkit.client.get(
            str(submission_url),
            follow_redirects=False,
        )
        if response.status_code != 302:
            # Allow redirection when submission page not public.
            response.raise_for_status()
        return response

    @codeforces_api_limits
    @backoff_on_exception
    async def _get_user_submissions(self, handle: str) -> Response:
        url = "https://codeforces.com/api/user.status"
        response = await self._toolkit.client.get(
            url, params={"handle": handle, "from": 1}
        )
        if response.status_code == 400:
            raise CrawlerError(
                f"Can not crawl Codeforces user '{handle}'.",
                response.text,
            )

        response.raise_for_status()
        return response

    @classmethod
    def _get_contest_id(cls, problem: dict[str, Any]) -> int:
        return int(problem["contestId"])

    @classmethod
    def _get_contest_type(cls, problem: dict[str, Any]) -> str:
        contest_id = cls._get_contest_id(problem)
        return "gym" if contest_id > 100_000 else "contest"

    @classmethod
    def _get_problem_id(cls, problem: dict[str, Any]) -> str:
        return problem["index"]

    @classmethod
    def _get_problem_url(cls, problem: dict[str, Any]) -> HttpUrl:
        contest_id = cls._get_contest_id(problem)
        problem_id = cls._get_problem_id(problem)
        contest_type = cls._get_contest_type(problem)
        url = f"https://codeforces.com/{contest_type}/{contest_id}/problem/{problem_id}"
        return HttpUrl(url)

    @classmethod
    def _get_submission_id(cls, submission: dict[str, Any]) -> str:
        return submission["id"]

    @classmethod
    def _get_submission_url(cls, submission: dict[str, Any]) -> HttpUrl:
        problem = submission["problem"]
        contest_type = cls._get_contest_type(problem=problem)
        contest_id = cls._get_contest_id(problem=problem)
        submission_id = cls._get_submission_id(submission=submission)
        url = f"https://codeforces.com/{contest_type}/{contest_id}/submission/{submission_id}"
        return HttpUrl(url)
