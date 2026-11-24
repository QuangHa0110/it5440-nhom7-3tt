"""Bí danh hóa định danh nhạy cảm. Muối nằm trong Z, không bao giờ vào repo."""

from __future__ import annotations

import hashlib
import hmac


class Aliaser:
    def __init__(self, salt: str) -> None:
        if not salt:
            raise ValueError("salt rỗng: bí danh sẽ đoán được")
        self._salt = salt.encode("utf-8")

    def alias(self, kind: str, value: str) -> str:
        digest = hmac.new(self._salt, f"{kind}\x1f{value}".encode(), hashlib.sha256).hexdigest()
        return f"{kind}-{digest[:10]}"
