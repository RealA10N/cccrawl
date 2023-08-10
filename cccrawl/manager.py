from collections.abc import AsyncIterable
from logging import getLogger
from typing import Final

from httpx import AsyncClient

from cccrawl.crawlers import CodeforcesCrawler, CsesCrawler
from cccrawl.crawlers.base import AnyCrawler
from cccrawl.db.base import Database
from cccrawl.models.any_integration import AnyIntegration
from cccrawl.models.integration import Platform
from cccrawl.models.submission import CrawledSubmission, Submission

logger = getLogger(__name__)

CRAWLER_PLATFORM_MAPPING: Final[dict[Platform, type[AnyCrawler]]] = {
    Platform.codeforces: CodeforcesCrawler,
    Platform.cses: CsesCrawler,
}

ALL_CRAWLERS = CRAWLER_PLATFORM_MAPPING.values()


class MainCrawler:
    def __init__(self, client: AsyncClient, db: Database) -> None:
        self._db = db
        self._crawlers: dict[Platform, AnyCrawler] = {
            platform: crawler_cls(client)
            for platform, crawler_cls in CRAWLER_PLATFORM_MAPPING.items()
        }

    async def crawl_integration(
        self, integration: AnyIntegration
    ) -> AsyncIterable[CrawledSubmission]:
        submissions = self._crawlers[integration.root.platform].crawl(integration.root)
        async for submission in submissions:
            yield submission

    async def crawl_integrations_new_submissions(
        self, integration: AnyIntegration
    ) -> AsyncIterable[Submission]:
        seen_ids = set()
        old_submissions = self._db.get_submissions_by_integration(integration)
        async for submission in old_submissions:
            seen_ids.add(submission.id)

        all_submissions = self.crawl_integration(integration)
        async for crawled_submission in all_submissions:
            if crawled_submission.id not in seen_ids:
                yield Submission.from_crawled(crawled_submission)

    async def crawl_integration_and_update_db(
        self, integration: AnyIntegration
    ) -> None:
        new_submissions = self.crawl_integrations_new_submissions(integration)
        async for submission in new_submissions:
            await self._db.upsert_submission(submission)

        integration.root.update_last_fetched()
        await self._db.upsert_integration(integration)

    async def crawl(self) -> None:
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
