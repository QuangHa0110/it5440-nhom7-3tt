"""Kho blob trên hệ tệp, đặt tên theo băm nội dung."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


class BlobStore:
    def __init__(self, root: Path) -> None:
        self._root = root
        root.mkdir(parents=True, exist_ok=True)

    def _path(self, ref: str) -> Path:
        return self._root / ref[:2] / ref

    def put(self, data: bytes) -> str:
        ref = hashlib.sha256(data).hexdigest()
        path = self._path(ref)
        if path.exists():
            return ref
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".tmp{os.getpid()}")
        tmp.write_bytes(data)
        tmp.replace(path)
        return ref

    def get(self, ref: str) -> bytes:
        return self._path(ref).read_bytes()

    def exists(self, ref: str) -> bool:
        return self._path(ref).exists()
