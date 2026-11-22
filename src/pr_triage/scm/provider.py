"""Lớp nhà cung cấp SCM: mọi thứ riêng của một máy chủ git nằm sau một giao diện (ADR 0021 D1)."""

from __future__ import annotations

import hashlib
import hmac
import re
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from pr_triage.core.ports import ScmPort
from pr_triage.core.scm import Event, GitRemote, OpenPr, PrApiPort, ScmKind

COMMAND = re.compile(r"(?im)^\s*(fp|tp)\s+[0-9a-f]{6,12}\b")
Headers = Mapping[str, str]


def lower_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {k.lower(): v for k, v in headers.items()}


def hmac_hex(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def verify_hmac(secret: str, body: bytes, header: str | None, prefix: str = "") -> bool:
    """So HMAC-SHA256 của thân với giá trị header (có thể có tiền tố `sha256=`), thời gian hằng."""
    if not secret or not header or not header.startswith(prefix):
        return False
    return hmac.compare_digest(hmac_hex(secret, body), header[len(prefix) :])


class ScmProvider(ABC):
    """Mỗi loại máy chủ cài đặt đủ các phương thức dưới đây. Lõi không biết loại nào đang chạy."""

    kind: ScmKind

    @property
    def webhook_path(self) -> str:
        return "/webhook" if self.kind is ScmKind.GITHUB else f"/webhook/{self.kind.value}"

    @abstractmethod
    def bot_login(self) -> str:
        """Tên tài khoản của bot, để bỏ qua sự kiện do chính nó gây ra."""

    @abstractmethod
    def token(self, installation_id: int = 0) -> str:
        """Token để gọi API và `git fetch`. `installation_id` chỉ có nghĩa với GitHub App."""

    @abstractmethod
    def api(self, token: str) -> PrApiPort: ...

    @abstractmethod
    def scm(self, token: str) -> ScmPort: ...

    @abstractmethod
    def remote(self, repo: str) -> GitRemote: ...

    @abstractmethod
    def verify_webhook(self, headers: Headers, body: bytes) -> bool:
        """`headers` có khóa chữ thường. Không có bí mật cấu hình thì luôn từ chối."""

    @abstractmethod
    def parse_webhook(self, headers: Headers, payload: dict[str, Any]) -> Event | None:
        """None nghĩa là bỏ qua sự kiện này."""

    @abstractmethod
    def open_prs(self, token: str, repo: str) -> list[OpenPr]: ...
