import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from logging import getLogger
from typing import Any, Generic, TypeAlias, TypeVar

from httpx import AsyncClient

from cccrawl.models.integration import Integration
from cccrawl.models.submission import CrawledSubmission

IntegrationT = TypeVar("IntegrationT", bound=Integration)

logger = getLogger(__name__)


class Crawler(ABC, Generic[IntegrationT]):
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    @abstractmethod
    async def crawl(
        self, integration: IntegrationT
    ) -> AsyncIterable[CrawledSubmission]:
        """Given the configuration of the user, returns a list of all
        submissions of the user."""


def retry(
    exception: type[Exception],
    start_sleep: int = 5,
    fail_factor: float = 2,
):
    def decorator(func):
        async def retry_func(*args, **kwargs):
            sleep = start_sleep
            while True:
                try:
                    return await func(*args, **kwargs)
                except exception:
                    logger.warning(
                        "Failed calling %s. Retrying in %.2f seconds.",
                        func,
                        sleep,
                        exc_info=True,
                    )
                await asyncio.sleep(sleep)
                sleep *= fail_factor

        return retry_func

    return decorator


AnyCrawler: TypeAlias = Crawler[Any]
