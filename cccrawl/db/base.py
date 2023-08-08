from abc import ABC, abstractmethod
from typing import AsyncGenerator, TypeAlias

from cccrawl.models.integration import Integration
from cccrawl.models.submission import Submission, UserSubmissions
from cccrawl.models.user import UserConfig

SubmissionsGenerator: TypeAlias = AsyncGenerator[Submission, None]
IntegrationsGenerator: TypeAlias = AsyncGenerator[Integration, None]


class Database(ABC):
    """An abstract database for accessing user information and configurations,
    and storing the solution data."""

    @abstractmethod
    async def generate_integrations(self) -> IntegrationsGenerator:
        """An infinite generator that should yield all integrations in the
        database, in a cycle. No users should be left outside the cycle, and
        newly registered users should be added at some point."""

    @abstractmethod
    async def update_integration_submissions(
        self, integration: Integration, submissions: SubmissionsGenerator
    ) -> None:
        """Overwrite the existing submissions set of the given integration with
        the given one in the database."""

    @abstractmethod
    async def get_submissions_by_integration(
        self, integration: Integration
    ) -> SubmissionsGenerator:
        """Retrieve list of previously scraped submissions for the provided
        user."""
