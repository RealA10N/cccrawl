import asyncio
from abc import ABC, abstractmethod
from logging import getLogger
from typing import Iterable

from httpx import AsyncClient

from cccrawl.models.submission import CrawledSubmission
from cccrawl.models.user import UserConfig

logger = getLogger(__name__)


class Crawler(ABC):
    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    @abstractmethod
    async def crawl(self, config: UserConfig) -> Iterable[CrawledSubmission]:
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
