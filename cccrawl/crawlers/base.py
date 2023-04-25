from abc import ABC, abstractmethod

from httpx import AsyncClient

from cccrawl.models.solution import SolutionUid
from cccrawl.models.user import UserConfig


class Crawler(ABC):

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    @abstractmethod
    async def crawl(self, config: UserConfig) -> set[SolutionUid]:
        """ Given the configuration of the user, crawl it's solutions are
        return their unique ids."""
