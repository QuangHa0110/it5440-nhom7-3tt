"""Nhà cung cấp GitHub. Nằm ở app/ vì dùng AppAuth và webhook của App (ADR 0012, 0021)."""

from __future__ import annotations

from typing import Any

import httpx

from pr_triage.app.auth import AppAuth
from pr_triage.app.webhook import parse_event, verify_signature
from pr_triage.bot.github import GitHubApi, GitHubScm
from pr_triage.core.errors import ScmError
from pr_triage.core.ports import ScmPort
from pr_triage.core.scm import Event, GitRemote, OpenPr, PrApiPort, ScmKind, split_repo
from pr_triage.scm.provider import Headers, ScmProvider


class GitHubProvider(ScmProvider):
    kind = ScmKind.GITHUB

    def __init__(
        self,
        api_url: str = "https://api.github.com",
        git_url_template: str = "https://github.com/{repo}.git",
        webhook_secret: str = "",
        auth: AppAuth | None = None,
        static_token: str = "",
        bot: str = "",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_url = api_url.rstrip("/")
        self._template = git_url_template
        self._secret = webhook_secret
        self._auth = auth
        self._static = static_token
        self._bot = bot
        self._transport = transport

    def bot_login(self) -> str:
        return self._auth.bot_login() if self._auth is not None else self._bot

    def token(self, installation_id: int = 0) -> str:
        if installation_id and self._auth is not None:
            return self._auth.installation_token(installation_id)
        if self._static:
            return self._static
        raise ScmError("GitHub: thiếu GITHUB_TOKEN hoặc cài đặt GitHub App")

    def api(self, token: str) -> PrApiPort:
        return GitHubApi(token, self._api_url, self._transport, backoff_s=1.0)

    def scm(self, token: str) -> ScmPort:
        return GitHubScm(token, self._api_url, self._transport, backoff_s=1.0)

    def remote(self, repo: str) -> GitRemote:
        _, path = split_repo(repo)
        return GitRemote(
            self._template.format(repo=path), "x-access-token", ("refs/pull/{n}/head",)
        )

    def verify_webhook(self, headers: Headers, body: bytes) -> bool:
        return verify_signature(self._secret, body, headers.get("x-hub-signature-256"))

    def parse_webhook(self, headers: Headers, payload: dict[str, Any]) -> Event | None:
        return parse_event(headers.get("x-github-event", ""), payload, self.bot_login())

    def open_prs(self, token: str, repo: str) -> list[OpenPr]:
        _, path = split_repo(repo)
        return GitHubApi(token, self._api_url, self._transport, backoff_s=1.0).open_prs(path)
