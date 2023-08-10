from collections.abc import AsyncIterable
from logging import getLogger

import backoff
from bs4 import BeautifulSoup
from httpx import HTTPError, Response

from cccrawl.crawlers.base import Crawler
from cccrawl.crawlers.error import CrawlerError
from cccrawl.integrations.cses import CsesIntegration
from cccrawl.models.any_integration import AnyIntegration
from cccrawl.models.problem import Problem
from cccrawl.models.submission import CrawledSubmission, SubmissionVerdict
from cccrawl.utils.ratelimit import ratelimit

logger = getLogger(__name__)


class CsesCrawler(Crawler[CsesIntegration]):
    async def crawl(
        self, integration: CsesIntegration
    ) -> AsyncIterable[CrawledSubmission]:
        if (user_number := integration.user_number) is None:
            logger.info("No available CSES user, skipping.")
            return

        response = await self._get_user_profile(user_number)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        table = soup.find("table")
        if table is None:
            raise CrawlerError(f"CSES user {user_number} does not exist")

        submitted_tags = table.find_all("a", {"class": {"full", "zero"}})

        for a_tag in submitted_tags:
            yield CrawledSubmission(
                integration=AnyIntegration(root=integration),
                problem=Problem(problem_url="https://cses.fi" + a_tag["href"][:-1]),
                verdict=SubmissionVerdict.accepted
                if "full" in a_tag["class"]
                else SubmissionVerdict.rejected,
            )

    @backoff.on_exception(backoff.expo, HTTPError, max_time=120)
    @ratelimit(calls=1, every=8)
    async def _get_user_profile(self, user_number: int) -> Response:
        url = f"https://cses.fi/problemset/user/{user_number}/"
        return await self._client.get(url)
