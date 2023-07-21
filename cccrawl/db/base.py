from abc import ABC, abstractmethod
from typing import AsyncGenerator

from cccrawl.models.submission import ProblemUid
from cccrawl.models.user import UserConfig


class Database(ABC):
    """An abstract database for accessing user information and configurations,
    and storing the solution data."""

    @abstractmethod
    async def generate_users(self) -> AsyncGenerator[UserConfig, None]:
        """An infinite generator that should yield all users in the database,
        in a cycle. No users should be left outside the cycle, and newly
        registered users should be added at some point."""

    @abstractmethod
    async def overwrite_user_submissions(
        self,
        user: UserConfig,
        submissions: list[Submission],
    ) -> None:
        """Overwrite the existing submissions set of the given user with the
        given one in the database."""

    @abstractmethod
    async def get_user_submissions(self, user: UserConfig) -> list[Submission]:
        """Retrieve list of previously scraped submissions for the provided
        user."""
