import asyncio
from logging import getLogger

from httpx import AsyncClient

from cccrawl.crawlers import CodeforcesCrawler, Crawler, CsesCrawler
from cccrawl.db.base import Database
from cccrawl.models.submission import CrawledSubmission, Submission
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

        async with asyncio.TaskGroup() as tg:
            for crawler in self._crawlers:
                tg.create_task(single_crawl(crawler))

        return submissions

    async def crawl_user_and_update_db(self, user: UserConfig) -> None:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(asyncio.sleep(WAIT_BETWEEN_CRAWLS))
            all_submissions_task = tg.create_task(self.crawl_user_submissions(user))
            old_submissions_task = tg.create_task(self._db.get_user_submissions(user))

        all_submissions = all_submissions_task.result()
        old_submissions = old_submissions_task.result()
        new_submissions = self._generate_new_submissions(
            all_submissions, old_submissions
        )

        return old_submissions + new_submissions

    async def crawl(self) -> None:
        async for user in self._db.generate_users():
            try:
                await self.crawl_user_and_update_db(user)
            except Exception:
                logger.error(
                    "Failed to crawl user %s, skipping to next user",
                    user.uid,
                    exc_info=True,
                )

    @classmethod
    def _generate_new_submissions(
        cls,
        all_submissions: list[CrawledSubmission],
        old_submissions: list[Submission],
    ) -> list[Submission]:
        """Receives a list of newly crawled submissions and the list of
        previously crawled submissions, filters out all submissions that
        already have been crawled, and returns only the list of new
        submissions."""
        raise NotImplementedError()
