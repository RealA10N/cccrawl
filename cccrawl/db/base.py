from abc import ABC, abstractmethod
from typing import AsyncGenerator

from cccrawl.models.solution import SolutionUid
from cccrawl.models.user import UserConfig


class Database(ABC):
    """ An abstract database for accessing user information and configurations,
    and storing the solution data."""

    @abstractmethod
    async def generate_users(self) -> AsyncGenerator[UserConfig, None]:
        """ An infinite generator that should yield all users in the database,
        in a cycle. No users should be left outside the cycle, and newly
        registered users should be added at some point."""

    @abstractmethod
    async def store_user_solutions(
        self,
        user: UserConfig,
        solutions: set[SolutionUid],
    ) -> None:
        """ Overwrite the existing solutions set of the given user with the
        given one in the database."""
