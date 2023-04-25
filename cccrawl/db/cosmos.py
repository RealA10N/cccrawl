from typing import AsyncGenerator, Type, TypeVar

from azure.cosmos import PartitionKey
from azure.cosmos.aio import CosmosClient

from cccrawl.db.base import Database
from cccrawl.models.solution import SolutionUid
from cccrawl.models.user import UserConfig

CosmosDatabaseT = TypeVar("CosmosDatabaseT", bound="CosmosDatabase")


class CosmosDatabase(Database):
    @classmethod
    async def init_database(
        cls: Type[CosmosDatabaseT], client: CosmosClient
    ) -> CosmosDatabaseT:
        users_db = await client.create_database_if_not_exists(id="users")

        configs_container = await users_db.create_container_if_not_exists(
            "configs", partition_key=PartitionKey("/id")
        )

        solutions_container = await users_db.create_container_if_not_exists(
            "solutions", partition_key=PartitionKey("/id")
        )

        return cls(users_db, configs_container, solutions_container)

    def __init__(self, users_db, configs_container, solutions_container) -> None:
        self._users_db = users_db
        self._configs_container = configs_container
        self._solutions_container = solutions_container

    async def generate_users(self) -> AsyncGenerator[UserConfig, None]:
        while True:
            async for item in self._configs_container.read_all_items():
                yield UserConfig.parse_obj(item)

    async def store_user_solutions(self, user: UserConfig, solutions: set[SolutionUid]):
        pass
