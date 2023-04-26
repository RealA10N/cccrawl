from logging import getLogger

from httpx import HTTPError

from cccrawl.crawlers.base import Crawler, retry
from cccrawl.crawlers.error import CrawlerError
from cccrawl.models.solution import SolutionUid
from cccrawl.models.user import UserConfig

logger = getLogger(__name__)


class CodeforcesCrawler(Crawler):
    @retry(exception=HTTPError, start_sleep=5, fail_factor=2)
    async def crawl(self, config: UserConfig) -> set[SolutionUid]:
        logger.info("Started crawling Codeforces user %s", config.codeforces)
        url = (
            f"https://codeforces.com/api/user.status?handle={config.codeforces}&from=1"
        )
        response = await self._client.get(url)

        if response.status_code == 400:
            raise CrawlerError("Can not crawl Codeforces user %s", config.codeforces)
        response.raise_for_status()

        submissions = response.json().get("result", [])
        return {
            self.generate_problem_uid(submission["problem"])
            for submission in submissions
            if submission["verdict"] == "OK"
        }

    @staticmethod
    def generate_problem_uid(problem) -> SolutionUid:
        contest_id = int(problem["contestId"])
        problem_id = problem["index"]
        contest_type = "gym" if contest_id > 100_000 else "contest"
        url = f"https://codeforces.com/{contest_type}/{contest_id}/problem/{problem_id}"
        return url
