from collections.abc import AsyncIterable
from datetime import datetime, timezone
from logging import getLogger
from typing import Any

import backoff
from httpx import HTTPError, Response
from pydantic import HttpUrl

from cccrawl.crawlers.base import Crawler
from cccrawl.crawlers.error import CrawlerError
from cccrawl.integrations.codeforces import CodeforcesIntegration
from cccrawl.models.any_integration import AnyIntegration
from cccrawl.models.problem import Problem
from cccrawl.models.submission import CrawledSubmission, SubmissionVerdict
from cccrawl.utils.ratelimit import ratelimit

logger = getLogger(__name__)


class CodeforcesCrawler(Crawler[CodeforcesIntegration]):
    async def crawl(
        self, integration: CodeforcesIntegration
    ) -> AsyncIterable[CrawledSubmission]:
        if (handle := integration.handle) is None:
            logger.info("No available Codeforces user, skipping.")
            return

        response = await self._get_user_submissions(handle)
        if response.status_code == 400:
            raise CrawlerError(
                "Can not crawl Codeforces user '%s': %s",
                handle,
                str(response.content),
            )
        response.raise_for_status()

        submissions = response.json().get("result", [])
        for sub in submissions:
            yield CrawledSubmission(
                integration=AnyIntegration(root=integration),
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

    @backoff.on_exception(backoff.expo, HTTPError, max_time=120)
    @ratelimit(calls=1, every=1)
    async def _get_user_submissions(self, handle: str) -> Response:
        url = "https://codeforces.com/api/user.status"
        return await self._client.get(url, params={"handle": handle, "from": 1})

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
