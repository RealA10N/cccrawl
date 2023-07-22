import asyncio
import logging
import os

import httpx
from azure.cosmos.aio import CosmosClient
from dotenv import load_dotenv

from cccrawl.db.cosmos import CosmosDatabase
from cccrawl.manager import MainCrawler

logging.basicConfig()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Disable info logs for azure cosmos, they are annoying!
azure_logger = logging.getLogger(
    "azure.core.pipeline.policies.http_logging_policy"
)
azure_logger.setLevel(logging.WARNING)

load_dotenv()


async def main():
    async with httpx.AsyncClient() as http_client:
        async with CosmosClient(
            os.getenv("COSMOS_ENDPOINT"), os.getenv("COSMOS_KEY")
        ) as cosmos_client:
            db = await CosmosDatabase.init_database(cosmos_client)
            await MainCrawler(http_client, db).crawl()


asyncio.run(main())
