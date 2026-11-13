"""Xác thực GitHub App: JWT RS256 cho App, token cài đặt có lưu đệm (ADR 0012 D2)."""

from __future__ import annotations

import datetime as dt
import threading
import time

import httpx
import jwt

from pr_triage.core.errors import ScmError


class AppAuth:
    def __init__(
        self,
        app_id: str,
        private_key: str,
        api_url: str = "https://api.github.com",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._app_id = app_id
        self._key = private_key
        self._api = api_url.rstrip("/")
        self._http = httpx.Client(timeout=30, transport=transport)
        self._cache: dict[int, tuple[str, float]] = {}
        self._lock = threading.Lock()
        self._login: str | None = None

    def app_jwt(self) -> str:
        now = int(time.time())
        payload = {"iat": now - 60, "exp": now + 540, "iss": self._app_id}
        return jwt.encode(payload, self._key, algorithm="RS256")

    def _call(self, method: str, path: str) -> dict[str, object]:
        token = self.app_jwt()
        resp = self._http.request(
            method,
            f"{self._api}{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        if resp.status_code >= 400:
            raise ScmError(f"GitHub {method} {path}: HTTP {resp.status_code}")
        data: dict[str, object] = resp.json()
        return data

    def installation_token(self, installation_id: int) -> str:
        with self._lock:
            cached = self._cache.get(installation_id)
            if cached and cached[1] - 60 > time.time():
                return cached[0]
            data = self._call("POST", f"/app/installations/{installation_id}/access_tokens")
            token = str(data["token"])
            expires = dt.datetime.fromisoformat(str(data["expires_at"]).replace("Z", "+00:00"))
            self._cache[installation_id] = (token, expires.timestamp())
            return token

    def bot_login(self) -> str:
        with self._lock:
            if self._login is None:
                slug = str(self._call("GET", "/app")["slug"])
                self._login = f"{slug}[bot]"
            return self._login
