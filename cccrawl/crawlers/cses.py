from bs4 import BeautifulSoup

from cccrawl.crawlers.base import Crawler
from cccrawl.models.solution import SolutionUid
from cccrawl.models.user import UserConfig


class CsesCrawler(Crawler):

    async def crawl(self, config: UserConfig) -> set[SolutionUid]:
        url = f'https://cses.fi/problemset/user/{config.cses}/'
        response = await self._client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        table = soup.find('table')
        solved_tags = table.find_all('a', {'class': 'full'})
        return {
            'https://cses.fi' + a_tag['href'][:-1]
            for a_tag in solved_tags
        }
