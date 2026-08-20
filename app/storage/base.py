from abc import ABC, abstractmethod
from typing import BinaryIO
from fastapi import UploadFile


class BaseFileStorage(ABC):
    """
    Abstract Base Class for file storage systems (Local, S3, GCS, Azure Blob).
    """

    @abstractmethod
    async def save_file(self, filename: str, upload_file: UploadFile) -> str:
        """
        Stream and persist uploaded file to storage.
        Returns unique storage identifier/path.
        """
        pass

    @abstractmethod
    def get_file_path(self, storage_key: str) -> str:
        """
        Resolve readable absolute path or URI for worker processing.
        """
        pass

    @abstractmethod
    def delete_file(self, storage_key: str) -> bool:
        """
        Safely delete file after processing.
        """
        pass
