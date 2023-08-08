from datetime import datetime, timezone
from logging import getLogger
from typing import Any

from httpx import HTTPError
from pydantic import HttpUrl

from cccrawl.crawlers.base import Crawler, retry
from cccrawl.crawlers.error import CrawlerError
from cccrawl.models.submission import CrawledSubmission, SubmissionVerdict
from cccrawl.models.problem import Problem
from cccrawl.models.user import UserConfig

logger = getLogger(__name__)


class CodeforcesCrawler(Crawler):
    @retry(exception=HTTPError, start_sleep=5, fail_factor=2)
    async def crawl(self, config: UserConfig) -> list[CrawledSubmission]:
        if (handle := config.codeforces) is None:
            logger.info("No available Codeforces user, skipping.")
            return list()

        logger.info("Started crawling Codeforces handle '%s'", handle)
        url = f"https://codeforces.com/api/user.status?handle={handle}&from=1"
        response = await self._client.get(url)

        if response.status_code == 400:
            raise CrawlerError(
                "Can not crawl Codeforces user '%s': %s",
                config.codeforces,
                str(response.content),
            )
        response.raise_for_status()

        submissions = response.json().get("result", [])
        return [
            CrawledSubmission(
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
            for sub in submissions
        ]

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
