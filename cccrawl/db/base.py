from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from typing import TypeAlias

from cccrawl.models.any_integration import AnyIntegration
from cccrawl.models.submission import Submission
from cccrawl.models.user import UserConfig


class Database(ABC):
    """An abstract database for accessing user information and configurations,
    and storing the solution data."""

    @abstractmethod
    async def generate_integrations(self) -> AsyncIterable[AnyIntegration]:
        """An infinite generator that should yield all integrations in the
        database, in a cycle. No integrations should be left outside the cycle, and
        newly registered users & integrations should be added at some point."""

    @abstractmethod
    async def upsert_submission(
        self, integration: AnyIntegration, submission: Submission
    ) -> None:
        """Insert a new submission to the database, or update an existing
        submission entry if a submisson with the same unique id already exists
        in the database."""

    @abstractmethod
    async def get_submissions_by_integration(
        self, integration: AnyIntegration
    ) -> AsyncIterable[Submission]:
        """Retrieve list of previously scraped submissions for the provided
        integration."""
