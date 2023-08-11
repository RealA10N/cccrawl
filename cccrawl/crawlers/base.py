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
    def crawl(self, integration: IntegrationT) -> AsyncIterable[CrawledSubmission]:
        """Given the configuration of the user, returns a list of all
        submissions of the user."""


AnyCrawler: TypeAlias = Crawler[Any]
