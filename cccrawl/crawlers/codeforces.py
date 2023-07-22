from datetime import datetime, timezone
from logging import getLogger
from typing import Any

from httpx import HTTPError

from cccrawl.crawlers.base import Crawler, retry
from cccrawl.crawlers.error import CrawlerError
from cccrawl.models.submission import CrawledSubmission, SubmissionVerdict
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
                problem_url=self._generate_problem_url(sub["problem"]),
                verdict=(
                    SubmissionVerdict.accepted
                    if sub["verdict"] == "OK"
                    else SubmissionVerdict.rejected
                ),
                submitted_at=datetime.fromtimestamp(
                    sub["creationTimeSeconds"], tz=timezone.utc
                ),
            )
            for sub in submissions
        ]

    @staticmethod
    def _generate_problem_url(problem: dict[str, Any]) -> str:
        contest_id = int(problem["contestId"])
        problem_id = problem["index"]
        contest_type = "gym" if contest_id > 100_000 else "contest"
        url = f"https://codeforces.com/{contest_type}/{contest_id}/problem/{problem_id}"
        return url
