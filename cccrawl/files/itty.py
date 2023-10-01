from typing import TextIO

from httpx import AsyncClient, HTTPStatusError
from pydantic import HttpUrl

from cccrawl.files.base import FileUploadError, FileUploadService


class IttyUploadService(FileUploadService):
    def __init__(self, key_length: int = 8, time_to_live: str = "30years") -> None:
        # WARNING: There is no argument validation here!
        # not implemented since it is kind messy and time consuming.
        self._key_length = key_length
        self._time_to_live = time_to_live

    async def upload(self, content: TextIO) -> HttpUrl:
        async with AsyncClient() as client:
            response = await client.post(
                url="https://ity.sh/",
                params={"ttl": self._time_to_live, "length": self._key_length},
                json=content.read(),
            )

        try:
            response.raise_for_status()
        except HTTPStatusError as exception:
            raise FileUploadError() from exception

        url: str = response.json()["url"]
        return HttpUrl(url)
