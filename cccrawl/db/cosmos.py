import os
from collections.abc import AsyncIterable
from logging import getLogger
from typing import Type, TypeVar

from azure.cosmos import PartitionKey
from azure.cosmos.aio import CosmosClient

from cccrawl.db.base import Database
from cccrawl.models.any_integration import AnyIntegration
from cccrawl.models.base import ModelId
from cccrawl.models.submission import Submission

CosmosDatabaseT = TypeVar("CosmosDatabaseT", bound="CosmosDatabase")


logger = getLogger(__name__)


class CosmosDatabase(Database):
    @classmethod
    async def init_database(
        cls: Type[CosmosDatabaseT], client: CosmosClient
    ) -> CosmosDatabaseT:
        db = await client.create_database_if_not_exists(
            id=os.getenv("ENV_NAME", default="dev")
        )

        configs_container = await db.create_container_if_not_exists(
            "configs", partition_key=PartitionKey("/id")
        )

        submissions_container = await db.create_container_if_not_exists(
            "submissions", partition_key=PartitionKey("/id")
        )

        integrations_container = await db.create_container_if_not_exists(
            "integrations", partition_key=PartitionKey("/id")
        )

        return cls(configs_container, submissions_container, integrations_container)

    def __init__(
        self, configs_container, submissions_container, integrations_container
    ) -> None:
        self._configs_container = configs_container
        self._submissions_container = submissions_container
        self._integrations_container = integrations_container

    async def generate_integrations(self) -> AsyncIterable[AnyIntegration]:
        while True:
            logger.info("Fetching all integrations (new cycle started)")
            async for item in self._integrations_container.read_all_items():
                integration = AnyIntegration.model_validate(item)
                yield integration

    async def upsert_submission(self, submission: Submission) -> None:
        logger.info("Upserting submission: %s", submission)
        body = submission.model_dump(mode="json")
        await self._submissions_container.upsert_item(body=body)

    async def upsert_integration(self, integration: AnyIntegration) -> None:
        logger.info("Upserting integration: %s", integration.root)
        body = integration.root.model_dump(mode="json")
        await self._integrations_container.upsert_item(body=body)

    async def get_collected_submission_ids(
        self, integration: AnyIntegration
    ) -> AsyncIterable[ModelId]:
        results = self._submissions_container.query_items(
            query="SELECT c.id FROM c WHERE c.integration.id = @integration_id",
            parameters=[{"name": "@integration_id", "value": integration.root.id}],
        )

        async for document in results:
            yield ModelId(document["id"])
