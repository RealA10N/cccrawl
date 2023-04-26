from logging import getLogger

from bs4 import BeautifulSoup
from httpx import HTTPError

from cccrawl.crawlers.base import Crawler, retry
from cccrawl.crawlers.error import CrawlerError
from cccrawl.models.solution import SolutionUid
from cccrawl.models.user import UserConfig

logger = getLogger(__name__)


class CsesCrawler(Crawler):
    @retry(exception=HTTPError, start_sleep=5, fail_factor=2)
    async def crawl(self, config: UserConfig) -> set[SolutionUid]:
        logger.info("Started crawling CSES user %s", config.cses)
        url = f"https://cses.fi/problemset/user/{config.cses}/"
        response = await self._client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        table = soup.find("table")
        if table is None:
            raise CrawlerError(f"CSES user {config.cses} does not exist")
        solved_tags = table.find_all("a", {"class": "full"})
        return {"https://cses.fi" + a_tag["href"][:-1] for a_tag in solved_tags}
