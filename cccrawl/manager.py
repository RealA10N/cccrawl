import asyncio
from logging import getLogger
from typing import Type

from httpx import AsyncClient

from cccrawl.crawlers import CodeforcesCrawler, Crawler, CsesCrawler
from cccrawl.db.base import Database
from cccrawl.models.solution import SolutionUid
from cccrawl.models.user import UserConfig

logger = getLogger(__name__)

ALL_CRAWLERS: list[Type[Crawler]] = [CodeforcesCrawler, CsesCrawler]
WAIT_BETWEEN_CRAWLS = 5


class MainCrawler:
    def __init__(self, client: AsyncClient, db: Database) -> None:
        self._db = db
        self._crawlers = [crawler_cls(client) for crawler_cls in ALL_CRAWLERS]

    async def crawl_user(self, user: UserConfig) -> set[SolutionUid]:
        collected_per_crawler = list()

        async def single_crawl(crawler: Crawler):
            collected_per_crawler.append(await crawler.crawl(user))

        async def time_task():
            await asyncio.sleep(WAIT_BETWEEN_CRAWLS)

        tasks = set()
        tasks.add(asyncio.create_task(time_task()))
        for crawler in self._crawlers:
            tasks.add(asyncio.create_task(single_crawl(crawler)))

        for task in tasks:
            await task

        return set.union(*collected_per_crawler)

    async def crawl(self) -> None:
        async for user in self._db.generate_users():
            try:
                logger.info("Started crawling user %s", user.uid)
                solutions = await self.crawl_user(user)
                await self._db.store_user_solutions(user, solutions)
            except Exception:
                logger.error(
                    "Failed to crawl user %s, skipping to next user",
                    user.uid,
                    exc_info=True,
                )
