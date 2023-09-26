from abc import ABC, abstractmethod
from typing import TextIO

from pydantic import HttpUrl


class FileUploadService(ABC):
    """An abstract implementation of a file upload service. Uploaded files
    should be publicly available."""

    @abstractmethod
    async def upload(self, content: TextIO) -> HttpUrl:
        """Upload the provided file content to a publicly available file
        hosting service, and return the URL of the uploaded file."""
