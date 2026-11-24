"""Máy chủ HTTP giả cho test nhà cung cấp SCM: bảng (phương thức, mẫu đường dẫn) -> hàm trả lời."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

import httpx

Handler = Callable[[httpx.Request, re.Match[str]], httpx.Response]


def ok(
    data: Any = None, status: int = 200, headers: dict[str, str] | None = None
) -> httpx.Response:
    if data is None:
        return httpx.Response(status, headers=headers)
    return httpx.Response(status, json=data, headers=headers)


def text(body: str, status: int = 200) -> httpx.Response:
    return httpx.Response(status, text=body)


class FakeHost:
    def __init__(self) -> None:
        self.routes: list[tuple[str, re.Pattern[str], Handler]] = []
        self.calls: list[tuple[str, str, dict[str, str], Any]] = []

    def on(self, method: str, pattern: str, handler: Handler | Any) -> None:
        h: Handler = handler if callable(handler) else (lambda _r, _m: ok(handler))
        self.routes.append((method, re.compile(pattern + "$"), h))

    def __call__(self, request: httpx.Request) -> httpx.Response:
        target = request.url.raw_path.decode()
        body: Any = None
        if request.content:
            try:
                body = json.loads(request.content)
            except ValueError:
                body = request.content.decode()
        self.calls.append((request.method, target, dict(request.headers), body))
        for method, rx, handler in self.routes:
            m = rx.match(target)
            if method == request.method and m:
                return handler(request, m)
        return httpx.Response(404, json={"message": f"no route {request.method} {target}"})

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self)

    def sent(self, method: str) -> list[tuple[str, Any]]:
        return [(t, b) for m, t, _h, b in self.calls if m == method]
