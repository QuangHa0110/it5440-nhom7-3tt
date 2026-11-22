"""Kiểu dữ liệu chung cho mọi máy chủ git (ADR 0021): loại máy chủ, mã định danh repo, PR."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from pr_triage.core.errors import ScmError
from pr_triage.core.models import JobKind


class ScmKind(StrEnum):
    GITHUB = "github"
    GITLAB = "gitlab"
    GITEA = "gitea"
    BITBUCKET = "bitbucket"


def split_repo(repo: str) -> tuple[ScmKind, str]:
    """Tách mã định danh đầy đủ: GitHub `owner/repo` (không tiền tố), loại khác `gitlab:g/p`."""
    prefix, sep, rest = repo.partition(":")
    if sep:
        try:
            kind = ScmKind(prefix)
        except ValueError:
            raise ScmError(f"loại máy chủ git không biết: '{prefix}' trong '{repo}'") from None
        if kind is ScmKind.GITHUB:
            raise ScmError("GitHub không dùng tiền tố; viết owner/repo")
        if not rest:
            raise ScmError(f"thiếu đường dẫn repo sau tiền tố: '{repo}'")
        return kind, rest
    return ScmKind.GITHUB, repo


def join_repo(kind: ScmKind, path: str) -> str:
    return path if kind is ScmKind.GITHUB else f"{kind.value}:{path}"


@dataclass(frozen=True)
class PrInfo:
    repo: str  # mã định danh đầy đủ
    number: int
    state: str
    merged: bool
    draft: bool
    author: str
    title: str
    base_ref: str
    base_sha: str
    head_sha: str
    head_repo: str
    changed_files: int


@dataclass(frozen=True)
class OpenPr:
    number: int
    head_sha: str
    base_ref: str
    draft: bool = False


@dataclass(frozen=True)
class GitRemote:
    """Cách lấy mã qua git: địa chỉ, tên người dùng khi xác thực HTTP, ref dự phòng của PR."""

    url: str
    username: str
    pr_ref_templates: tuple[str, ...]

    def pr_refs(self, number: int) -> list[str]:
        return [t.format(n=number) for t in self.pr_ref_templates]


@dataclass(frozen=True)
class Event:
    """Sự kiện webhook đã chuẩn hóa. `repo` là mã định danh đầy đủ."""

    kind: JobKind
    repo: str
    pr_number: int
    installation_id: int
    key: str
    draft: bool = False
    sender: str = ""


class PrApiPort(Protocol):
    """Lời gọi chỉ đọc cần cho bot, riêng cho từng máy chủ."""

    def get_pr(self, repo: str, number: int) -> PrInfo: ...

    def merge_base(self, repo: str, base: str, head: str) -> str: ...

    def get_file(self, repo: str, path: str, ref: str) -> str | None: ...
