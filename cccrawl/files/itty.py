from typing import TextIO

from httpx import AsyncClient
from pydantic import HttpUrl

from cccrawl.files.base import FileUploadService


class IttyUploadService(FileUploadService):
    async def upload(self, content: TextIO) -> HttpUrl:
        async with AsyncClient() as client:
            response = await client.post(
                url="https://ity.sh/",
                params={"ttl": "30years"},
                json=content.read(),
            )
        response.raise_for_status()
        url: str = response.json()["url"]
        return HttpUrl(url)
