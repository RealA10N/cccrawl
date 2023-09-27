from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from logging import getLogger
from typing import Any, Generic, TypeAlias, TypeVar

from cccrawl.crawlers.toolkit import CrawlerToolkit
from cccrawl.models.integration import Integration
from cccrawl.models.submission import CrawledSubmission, Submission

IntegrationT = TypeVar("IntegrationT", bound=Integration)
CrawledSubmissionT = TypeVar("CrawledSubmissionT", bound=CrawledSubmission)
SubmissionT = TypeVar("SubmissionT", bound=Submission)

logger = getLogger(__name__)


class Crawler(ABC, Generic[IntegrationT, CrawledSubmissionT, SubmissionT]):
    def __init__(self, toolkit: CrawlerToolkit) -> None:
        self._toolkit = toolkit

    @abstractmethod
    async def crawl(
        self, integration: IntegrationT
    ) -> AsyncIterable[CrawledSubmissionT]:
        """Provided an integration, this method should crawl a subset of the
        integration, in which it is guaranteed that all new submissions appear
        in such subset. In particular, it is OK to crawl submissions that have
        already been seen before (that have been reported with previous calls
        to the same function, or that are already stored in the database).
        The implementation logic, of how to filter out new submissions and
        query them is left for to the implementation of the specific platform
        crawlers."""

    @abstractmethod
    async def finalize_new_submission(
        self, crawled_submission: CrawledSubmissionT
    ) -> SubmissionT:
        """Provided a new crawled submission with only partial data available,
        this method should crawl additional data that is considered 'expensive',
        and convert it into a full 'Submission' instance.
        Note: This method is called only once per submission, before it is
        inserted into the database. It may leave traces and cause side effects,
        like for example, copying the source code of the submission into a
        CodeCoach-managed database."""


AnyCrawler: TypeAlias = Crawler[Any, Any, Any]
