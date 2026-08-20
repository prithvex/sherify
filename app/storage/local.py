import os
import uuid
import aiofiles
from fastapi import UploadFile
from app.core.config import settings
from app.storage.base import BaseFileStorage


class LocalFileStorage(BaseFileStorage):
    """
    Local filesystem storage implementation with chunked streaming writes.
    """

    def __init__(self, base_dir: str = settings.STORAGE_LOCAL_DIR):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    async def save_file(self, filename: str, upload_file: UploadFile) -> str:
        unique_name = f"{uuid.uuid4()}_{filename.replace(' ', '_')}"
        file_path = os.path.join(self.base_dir, unique_name)

        # Stream in 64KB chunks to avoid reading entire file into RAM
        async with aiofiles.open(file_path, "wb") as out_file:
            while chunk := await upload_file.read(64 * 1024):
                await out_file.write(chunk)

        # Reset cursor for any subsequent reads
        await upload_file.seek(0)
        return file_path

    def get_file_path(self, storage_key: str) -> str:
        return storage_key

    def delete_file(self, storage_key: str) -> bool:
        try:
            if os.path.exists(storage_key):
                os.remove(storage_key)
                return True
        except Exception:
            pass
        return False


local_file_storage = LocalFileStorage()
