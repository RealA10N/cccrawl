from asyncio import TaskGroup
from collections.abc import AsyncIterable, Mapping
from logging import getLogger

from cccrawl.crawlers.base import AnyCrawler
from cccrawl.db.base import Database
from cccrawl.models.any_integration import AnyIntegration
from cccrawl.models.integration import Platform
from cccrawl.models.submission import CrawledSubmission

logger = getLogger(__name__)


class MainCrawler:
    def __init__(
        self,
        db: Database,
        crawlers: Mapping[Platform, AnyCrawler],
    ) -> None:
        self._db = db
        self._crawlers = crawlers

    async def crawl_integration_new_submissions(
        self, integration: AnyIntegration
    ) -> AsyncIterable[CrawledSubmission]:
        """Yields all submissions that are new and do not appear in the database."""

        seen_ids = set()
        async for submission_id in self._db.get_collected_submission_ids(integration):
            seen_ids.add(submission_id)

        crawler = self._get_crawler_for_integration(integration)

        async for crawled_submission in crawler.crawl(integration.root):
            if crawled_submission.id not in seen_ids:
                yield crawled_submission

    async def crawl_integration_and_update_db(
        self, integration: AnyIntegration
    ) -> None:
        new_submissions_gen = self.crawl_integration_new_submissions(integration)
        crawler = self._get_crawler_for_integration(integration)
        integration.root.update_last_fetched()

        async with TaskGroup() as tg:
            async for crawled_submission in new_submissions_gen:
                tg.create_task(
                    self._finalize_submission_and_update_db(
                        crawler,
                        crawled_submission,
                    )
                )

        await self._db.upsert_integration(integration)

    async def crawl(self) -> None:
        await self._load_all_crawlers()
        integrations = self._db.generate_integrations()
        async for integration in integrations:
            try:
                await self.crawl_integration_and_update_db(integration)
            except Exception:
                logger.error(
                    "Failed to crawl integration %s",
                    integration,
                    exc_info=True,
                )

    async def _load_all_crawlers(self) -> None:
        async with TaskGroup() as tg:
            for crawler in self._crawlers.values():
                tg.create_task(crawler.load())

    def _get_crawler_for_integration(self, integration: AnyIntegration) -> AnyCrawler:
        return self._crawlers[integration.root.platform]

    async def _finalize_submission_and_update_db(
        self,
        crawler: AnyCrawler,
        crawled_submission: CrawledSubmission,
    ) -> None:
        finalized_submission = await crawler.finalize_new_submission(crawled_submission)
        await self._db.upsert_submission(finalized_submission)
