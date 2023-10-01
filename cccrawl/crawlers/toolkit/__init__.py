from typing import NamedTuple

from httpx import AsyncClient

from cccrawl.files.base import FileUploadService


class CrawlerToolkit(NamedTuple):
    client: AsyncClient
    file_uploader: FileUploadService
