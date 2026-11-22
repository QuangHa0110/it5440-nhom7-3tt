"""Khách HTTP dùng chung cho các máy chủ git: thử lại có lùi, che token trong lỗi."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from typing import Any

import httpx

from pr_triage.core.errors import ScmError

_RETRY = {429, 500, 502, 503, 504}
MAX_PAGES = 50


class RestClient:
    def __init__(
        self,
        name: str,
        base_url: str,
        auth_headers: Callable[[], Mapping[str, str]],
        transport: httpx.BaseTransport | None = None,
        backoff_s: float = 1.0,
        secrets: tuple[str, ...] = (),
    ) -> None:
        self._name = name
        self._base = base_url.rstrip("/")
        self._auth = auth_headers
        self._http = httpx.Client(timeout=30, transport=transport)
        self._backoff = backoff_s
        self._secrets = tuple(s for s in secrets if s)

    def _scrub(self, text: str) -> str:
        for s in self._secrets:
            text = text.replace(s, "***")
        return text

    def raw(self, method: str, path: str, **kw: Any) -> httpx.Response:
        """Gọi và trả về phản hồi thô; lỗi 4xx (trừ 429) trả về để nơi gọi quyết định."""
        last = ""
        for attempt in range(1, 4):
            try:
                resp = self._http.request(
                    method, f"{self._base}{path}", headers=dict(self._auth()), **kw
                )
            except httpx.HTTPError as exc:
                last = type(exc).__name__
            else:
                if resp.status_code not in _RETRY:
                    return resp
                last = f"HTTP {resp.status_code} {self._scrub(resp.text)[:200]}"
            if attempt < 3:
                time.sleep(self._backoff * attempt)
        raise ScmError(f"{self._name} {method} {path}: {last}")

    def json(self, method: str, path: str, **kw: Any) -> Any:
        resp = self.raw(method, path, **kw)
        if resp.status_code >= 400:
            body = self._scrub(resp.text)[:200]
            raise ScmError(f"{self._name} {method} {path}: HTTP {resp.status_code} {body}")
        return resp.json() if resp.content else None
