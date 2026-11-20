"""File storage behind a tiny interface. Swap LocalStorage for an S3 version on AWS."""
from pathlib import Path

from .config import settings


class LocalStorage:
    def __init__(self, root: str):
        self.root = Path(root) / "raw"
        self.root.mkdir(parents=True, exist_ok=True)

    def save_file(self, name: str, data: bytes) -> str:
        path = self.root / name
        path.write_bytes(data)
        return str(path)

    def read_file(self, name: str) -> bytes:
        return (self.root / name).read_bytes()


storage = LocalStorage(settings.data_dir)
