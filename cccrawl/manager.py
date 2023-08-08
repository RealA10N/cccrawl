import asyncio
from logging import getLogger
from typing import Final, Any
from httpx import AsyncClient

from cccrawl.crawlers import CodeforcesCrawler, Crawler, CsesCrawler
from cccrawl.crawlers.base import AnyCrawler, CrawledSubmissionsGenerator
from cccrawl.db.base import Database, SubmissionsGenerator
from cccrawl.models.integration import Integration, Platform
from cccrawl.models.submission import (
    CrawledSubmission,
    Submission,
    UserSubmissions,
)
from cccrawl.models.user import UserConfig
from cccrawl.utils import current_datetime

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
            for platform, crawler_cls in CRAWLER_PLATFORM_MAPPING
        }

    async def crawl_integraion(
        self, integraion: Integration
    ) -> CrawledSubmissionsGenerator:
        submissions = self._crawlers[integraion.platform].crawl(integraion)
        async for submission in submissions:
            yield submission

    async def crawl_integrations_new_submissions(
        self, integration: Integration
    ) -> SubmissionsGenerator:
        seen_uids = set()
        async for submission in self._db.get_submissions_by_integration(integration):
            seen_uids.add(submission.uid)

        submissions_generator = self.crawl_integraion(integration)
        async for crawled_submission in submissions_generator:
            if crawled_submission.uid not in seen_uids:
                yield Submission.from_crawled(crawled_submission)

    async def crawl_integration_and_update_db(self, integration: Integration) -> None:
        new_submissions = self.crawl_integrations_new_submissions(integration)
        async for submission in new_submissions:
            await self._db.upsert_submission(integration, submission)

    async def crawl(self) -> None:
        async for integration in self._db.generate_integrations():
            try:
                await self.crawl_integration_and_update_db(integration)
            except Exception:
                logger.error(
                    "Failed to crawl integration %s",
                    integration,
                    exc_info=True,
                )
