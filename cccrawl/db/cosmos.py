from collections.abc import AsyncIterable
from logging import getLogger
from typing import Type, TypeVar

from azure.cosmos import PartitionKey
from azure.cosmos.aio import CosmosClient

from cccrawl.db.base import Database
from cccrawl.models.any_integration import AnyIntegration
from cccrawl.models.submission import Submission
from cccrawl.models.user import UserConfig

CosmosDatabaseT = TypeVar("CosmosDatabaseT", bound="CosmosDatabase")


logger = getLogger(__name__)


class CosmosDatabase(Database):
    @classmethod
    async def init_database(
        cls: Type[CosmosDatabaseT], client: CosmosClient
    ) -> CosmosDatabaseT:
        users_db = await client.create_database_if_not_exists(id="dev")

        configs_container = await users_db.create_container_if_not_exists(
            "configs", partition_key=PartitionKey("/id")
        )

        submissions_container = await users_db.create_container_if_not_exists(
            "submissions", partition_key=PartitionKey("/id")
        )

        return cls(users_db, configs_container, submissions_container)

    def __init__(self, users_db, configs_container, submissions_container) -> None:
        self._users_db = users_db
        self._configs_container = configs_container
        self._submissions_container = submissions_container

    async def generate_integrations(self) -> AsyncIterable[AnyIntegration]:
        while True:
            logger.info("Fetching all integrations (new cycle started)")
            async for item in self._configs_container.read_all_items():
                user = UserConfig.model_validate(item)
                for integration in user.integrations:
                    yield integration

    async def upsert_submission(
        self, integration: AnyIntegration, submission: Submission
    ) -> None:
        logger.info("Upserting submission: %s", submission)
        body = submission.model_dump(mode="json")
        await self._submissions_container.upsert_item(body=body)

    async def get_submissions_by_integration(
        self, integration: AnyIntegration
    ) -> AsyncIterable[Submission]:
        integration_id = integration.root.id
        query = f"SELECT * FROM c WHERE c.integration.id = '{integration_id}'"
        results = self._submissions_container.query_items(query)

        async for document in results:
            yield Submission.model_validate(document)
