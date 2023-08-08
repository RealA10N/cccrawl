from abc import ABC, abstractmethod
from typing import IO

from yarl import URL


class FileUploadService(ABC):
    """An abstract implementation of a file upload service. Uploaded files
    should be publicly avaliable."""

    @abstractmethod
    async def upload(self, content: IO) -> URL:
        """Upload the provided file content to a publicly avaliable file
        hosting service, and return the URL of the uploaded file."""
