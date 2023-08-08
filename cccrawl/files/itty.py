import json
from typing import TextIO

from httpx import AsyncClient
from yarl import URL

from cccrawl.files.base import FileUploadService


class IttyUploadService(FileUploadService):
    async def upload(self, content: TextIO) -> URL:
        async with AsyncClient() as client:
            response = await client.post(
                url="https://ity.sh/",
                params={"ttl": "30years"},
                json=content.read(),
            )
        assert response.status_code == 200
        return response.json()["url"]
