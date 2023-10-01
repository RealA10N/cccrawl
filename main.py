import asyncio
import logging
import os

import httpx
from azure.cosmos.aio import CosmosClient
from dotenv import load_dotenv

from cccrawl.crawlers.codeforces import CodeforcesCrawler
from cccrawl.crawlers.cses import CsesCrawler, CsesCredentials
from cccrawl.crawlers.toolkit import CrawlerToolkit
from cccrawl.db.cosmos import CosmosDatabase
from cccrawl.files.itty import IttyUploadService
from cccrawl.manager import MainCrawler
from cccrawl.models.integration import Platform

logging.basicConfig()

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Disable info logs for azure cosmos, they are annoying!
azure_logger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
azure_logger.setLevel(logging.WARNING)

load_dotenv()


async def main():
    async with httpx.AsyncClient() as http_client:
        toolkit = CrawlerToolkit(
            client=http_client,
            file_uploader=IttyUploadService(key_length=16),
        )

        crawlers_mapping = {
            Platform.cses: CsesCrawler(
                toolkit=toolkit,
                credentials=CsesCredentials(
                    username=os.getenv("CSES_USERNAME"),
                    password=os.getenv("CSES_PASSWORD"),
                ),
            ),
            Platform.codeforces: CodeforcesCrawler(
                toolkit=toolkit,
            ),
        }

        async with CosmosClient(
            os.getenv("COSMOS_ENDPOINT"), os.getenv("COSMOS_KEY")
        ) as cosmos_client:
            db = await CosmosDatabase.init_database(cosmos_client)
            await MainCrawler(
                db=db,
                crawlers=crawlers_mapping,
            ).crawl()


asyncio.run(main())
