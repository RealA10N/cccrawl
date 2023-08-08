from logging import getLogger
from typing import Literal

from bs4 import BeautifulSoup
from httpx import HTTPError
from pydantic import computed_field, conint

from cccrawl.crawlers.base import Crawler, retry
from cccrawl.crawlers.error import CrawlerError
from cccrawl.models.base import ModelUid
from cccrawl.models.integration import Integration, Platform
from cccrawl.models.problem import Problem
from cccrawl.models.submission import CrawledSubmission, SubmissionVerdict
from cccrawl.models.user import UserConfig

logger = getLogger(__name__)


class CsesIntegration(Integration):
    platform: Literal[Platform.cses]
    user_number: conint(strict=True, gt=0, le=10_000_000)

    @computed_field
    @property
    def uid(self) -> ModelUid:
        return ModelUid(self._hash_tokens(self.platform.value, self.user_number))


class CsesCrawler(Crawler):
    @retry(exception=HTTPError, start_sleep=5, fail_factor=2)
    async def crawl(self, config: UserConfig) -> list[CrawledSubmission]:
        if (handle := config.cses) is None:
            logger.info("No available CSES user, skipping.")
            return list()

        logger.info("Started crawling CSES user '%s'", handle)
        url = f"https://cses.fi/problemset/user/{handle}/"
        response = await self._client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        table = soup.find("table")
        if table is None:
            raise CrawlerError(f"CSES user '{handle}' does not exist")
        solved_tags = table.find_all("a", {"class": "full"})
        return [
            CrawledSubmission(
                problem=Problem(problem_url="https://cses.fi" + a_tag["href"][:-1]),
                verdict=SubmissionVerdict.accepted,
            )
            for a_tag in solved_tags
        ]
