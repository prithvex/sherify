from app.storage.base import BaseFileStorage
from app.storage.local import LocalFileStorage, local_file_storage


def get_file_storage() -> BaseFileStorage:
    """
    Factory function returning the configured FileStorage backend.
    """
    return local_file_storage


__all__ = [
    "BaseFileStorage",
    "LocalFileStorage",
    "local_file_storage",
    "get_file_storage",
]
