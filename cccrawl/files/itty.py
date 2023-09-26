from typing import TextIO

from httpx import AsyncClient, HTTPStatusError
from pydantic import HttpUrl

from cccrawl.files.base import FileUploadError, FileUploadService


class IttyUploadService(FileUploadService):
    async def upload(self, content: TextIO) -> HttpUrl:
        async with AsyncClient() as client:
            response = await client.post(
                url="https://ity.sh/",
                params={"ttl": "30years"},
                json=content.read(),
            )

        try:
            response.raise_for_status()
        except HTTPStatusError:
            raise FileUploadError()

        url: str = response.json()["url"]
        return HttpUrl(url)
