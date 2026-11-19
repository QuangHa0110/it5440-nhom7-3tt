"""Cấu hình máy chủ từ biến môi trường. Bí mật không bao giờ in ra."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from pr_triage.core.delivery import (
    Channel,
    DeliveryConfigError,
    RepoAllowList,
    RepoGate,
    RoutePolicy,
)


class SettingsError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    app_id: str
    private_key: str = field(repr=False)
    webhook_secret: str = field(repr=False)
    alias_salt: str = field(repr=False)
    api_url: str = "https://api.github.com"
    git_url_template: str = "https://github.com/{repo}.git"
    db: str = "data/app/store.sqlite"
    workers: int = 2
    pipeline_workers: int = 4
    rules: tuple[str, ...] = ("configs/semgrep/java-injection.yml",)
    catalog: str = "configs/context/java.yml"
    engine: str = "graph"
    admin_token: str = field(default="", repr=False)
    allowed_repos: tuple[str, ...] = ()
    routes: str = ""  # PR_TRIAGE_ROUTES, ADR 0018 D4
    max_body_bytes: int = 5_000_000
    snippet_radius: int = 10  # bán kính đoạn mã của cách B
    budget_pr_tokens: int = (
        200_000  # trần token của engine LLM (xem TD-4: cộng dồn theo tiến trình)
    )

    def gate(self) -> RepoGate:
        """Danh sách rỗng cho mọi repo (tương thích); định tuyến chỉ cho kênh GitHub App."""
        return RepoGate(RepoAllowList(self.allowed_repos, empty_allows_all=True), self._routes())

    def _routes(self) -> RoutePolicy:
        try:
            return RoutePolicy.parse(self.routes)
        except DeliveryConfigError as exc:
            raise SettingsError(f"PR_TRIAGE_ROUTES: {exc}") from exc

    def repo_allowed(self, repo: str) -> bool:
        return self.gate().admits(Channel.GITHUB_APP, repo)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        e = os.environ if env is None else env
        key = e.get("GITHUB_APP_PRIVATE_KEY", "").replace("\\n", "\n")
        if not key and e.get("GITHUB_APP_PRIVATE_KEY_PATH"):
            key = Path(e["GITHUB_APP_PRIVATE_KEY_PATH"]).read_text("utf-8")
        missing = [
            name
            for name, val in [
                ("GITHUB_APP_ID", e.get("GITHUB_APP_ID", "")),
                ("GITHUB_APP_PRIVATE_KEY hoặc GITHUB_APP_PRIVATE_KEY_PATH", key),
                ("GITHUB_WEBHOOK_SECRET", e.get("GITHUB_WEBHOOK_SECRET", "")),
                ("PR_TRIAGE_ALIAS_SALT", e.get("PR_TRIAGE_ALIAS_SALT", "")),
            ]
            if not val
        ]
        if missing:
            raise SettingsError("thiếu cấu hình: " + ", ".join(missing))

        def csv(name: str, default: str = "") -> tuple[str, ...]:
            return tuple(x.strip() for x in e.get(name, default).split(",") if x.strip())

        try:
            RoutePolicy.parse(e.get("PR_TRIAGE_ROUTES", ""))
        except DeliveryConfigError as exc:
            raise SettingsError(f"PR_TRIAGE_ROUTES: {exc}") from exc
        return cls(
            app_id=e["GITHUB_APP_ID"],
            private_key=key,
            webhook_secret=e["GITHUB_WEBHOOK_SECRET"],
            alias_salt=e["PR_TRIAGE_ALIAS_SALT"],
            api_url=e.get("GITHUB_API_URL", cls.api_url).rstrip("/"),
            git_url_template=e.get("GITHUB_GIT_URL_TEMPLATE", cls.git_url_template),
            db=e.get("PR_TRIAGE_DB", cls.db),
            workers=int(e.get("PR_TRIAGE_WORKERS", "2")),
            pipeline_workers=int(e.get("PR_TRIAGE_PIPELINE_WORKERS", "4")),
            rules=csv("PR_TRIAGE_RULES", ",".join(cls.rules)) or cls.rules,
            catalog=e.get("PR_TRIAGE_CATALOG", cls.catalog),
            engine=e.get("PR_TRIAGE_ENGINE", cls.engine),
            admin_token=e.get("PR_TRIAGE_ADMIN_TOKEN", ""),
            allowed_repos=csv("PR_TRIAGE_ALLOWED_REPOS"),
            routes=e.get("PR_TRIAGE_ROUTES", ""),
            snippet_radius=int(e.get("PR_TRIAGE_SNIPPET_RADIUS", "10")),
            budget_pr_tokens=int(e.get("PR_TRIAGE_BUDGET_PR_TOKENS", "200000")),
        )
