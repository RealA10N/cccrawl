import asyncio
from logging import getLogger

from httpx import AsyncClient

from cccrawl.crawlers import CodeforcesCrawler, Crawler, CsesCrawler
from cccrawl.db.base import Database
from cccrawl.models.submission import CrawledSubmission
from cccrawl.models.user import UserConfig

logger = getLogger(__name__)

ALL_CRAWLERS: list[type[Crawler]] = [CodeforcesCrawler, CsesCrawler]
WAIT_BETWEEN_CRAWLS = 8


class MainCrawler:
    def __init__(self, client: AsyncClient, db: Database) -> None:
        self._db = db
        self._crawlers = [crawler_cls(client) for crawler_cls in ALL_CRAWLERS]

    async def crawl_user_submissions(
        self,
        user: UserConfig,
    ) -> list[CrawledSubmission]:
        """Crawl submissions from all crawlers to the given user
        synchronically."""

        submissions = list()

        async def single_crawl(crawler: Crawler):
            submissions.extend(await crawler.crawl(user))

        async def time_task():
            await asyncio.sleep(WAIT_BETWEEN_CRAWLS)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(time_task())
            for crawler in self._crawlers:
                tg.create_task(single_crawl(crawler))

        return submissions

    async def crawl(self) -> None:
        async for user in self._db.generate_users():
            try:
                logger.info("Started crawling user %s", user.uid)
                await self.crawl_user(user)
            except Exception:
                logger.error(
                    "Failed to crawl user %s, skipping to next user",
                    user.uid,
                    exc_info=True,
                )
