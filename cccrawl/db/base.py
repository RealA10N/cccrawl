from abc import ABC, abstractmethod
from collections.abc import AsyncIterable

from cccrawl.models.any_integration import AnyIntegration
from cccrawl.models.base import ModelId
from cccrawl.models.submission import Submission


class Database(ABC):
    """An abstract database for accessing user information and configurations,
    and storing the solution data."""

    @abstractmethod
    def generate_integrations(self) -> AsyncIterable[AnyIntegration]:
        """An infinite generator that should yield all integrations in the
        database, in a cycle. No integrations should be left outside the cycle, and
        newly registered users & integrations should be added at some point."""

    @abstractmethod
    async def upsert_integration(self, integration: AnyIntegration) -> None:
        """Update integration details on the database. Used for example to update
        the last fetch time, or update status of an integration."""

    @abstractmethod
    async def upsert_submission(self, submission: Submission) -> None:
        """Insert a new submission to the database, or update an existing
        submission entry if a submission with the same unique id already exists
        in the database."""

    @abstractmethod
    def get_collected_submission_ids(
        self, integration: AnyIntegration
    ) -> AsyncIterable[ModelId]:
        """Retrieve IDs of all previously crawled submissions under the provided
        integration. TODO: optimize."""
