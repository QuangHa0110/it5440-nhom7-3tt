"""Dựng nhà cung cấp SCM từ biến môi trường (ADR 0021 D3). Bí mật không bao giờ vào `repr`."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

import httpx

from pr_triage.app.github_provider import GitHubProvider
from pr_triage.core.errors import ScmError
from pr_triage.core.scm import ScmKind, split_repo
from pr_triage.scm.bitbucket import BitbucketServerProvider
from pr_triage.scm.gitea import GiteaProvider
from pr_triage.scm.gitlab import GitLabProvider
from pr_triage.scm.provider import ScmProvider

_ENV_PREFIX = {
    ScmKind.GITLAB: "PR_TRIAGE_GITLAB",
    ScmKind.GITEA: "PR_TRIAGE_GITEA",
    ScmKind.BITBUCKET: "PR_TRIAGE_BITBUCKET",
}


@dataclass(frozen=True)
class HostConfig:
    """Một máy chủ git tự lưu trữ (GitLab, Gitea, Bitbucket Server)."""

    kind: ScmKind
    url: str
    token: str = field(default="", repr=False)
    webhook_secret: str = field(default="", repr=False)
    bot_login: str = ""


def host_configs(env: Mapping[str, str] | None = None) -> tuple[HostConfig, ...]:
    """Máy chủ nào có `PR_TRIAGE_<LOẠI>_URL` thì được bật."""
    e = os.environ if env is None else env
    out: list[HostConfig] = []
    for kind, prefix in _ENV_PREFIX.items():
        url = e.get(f"{prefix}_URL", "").strip().rstrip("/")
        if url:
            out.append(
                HostConfig(
                    kind, url, e.get(f"{prefix}_TOKEN", ""), e.get(f"{prefix}_WEBHOOK_SECRET", ""),
                    e.get(f"{prefix}_BOT_LOGIN", ""),
                )
            )  # fmt: skip
    return tuple(out)


def build_host_provider(
    cfg: HostConfig, transport: httpx.BaseTransport | None = None
) -> ScmProvider:
    args = (cfg.url, cfg.token, cfg.webhook_secret, cfg.bot_login)
    if cfg.kind is ScmKind.GITLAB:
        return GitLabProvider(*args, transport=transport)
    if cfg.kind is ScmKind.GITEA:
        return GiteaProvider(*args, transport=transport)
    if cfg.kind is ScmKind.BITBUCKET:
        return BitbucketServerProvider(*args, transport=transport)
    raise ScmError(f"không có nhà cung cấp tự lưu trữ cho {cfg.kind.value}")


def provider_for_repo(repo: str, env: Mapping[str, str] | None = None) -> ScmProvider:
    """Nhà cung cấp cho một mã định danh repo, dùng ở CLI và Jenkins (token tĩnh từ môi trường)."""
    e = os.environ if env is None else env
    kind, _ = split_repo(repo)
    if kind is ScmKind.GITHUB:
        return GitHubProvider(
            api_url=e.get("GITHUB_API_URL", "https://api.github.com"),
            git_url_template=e.get("GITHUB_GIT_URL_TEMPLATE", "https://github.com/{repo}.git"),
            static_token=e.get("GITHUB_TOKEN", ""),
        )
    for cfg in host_configs(e):
        if cfg.kind is kind:
            return build_host_provider(cfg)
    raise ScmError(f"chưa cấu hình {_ENV_PREFIX[kind]}_URL cho repo '{repo}'")
