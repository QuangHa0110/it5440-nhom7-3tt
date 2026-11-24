"""Lấy hai bản mã (head và merge-base) từ một repo Git cục bộ, chỉ đọc."""

from __future__ import annotations

import datetime as dt
import re
import subprocess
import tarfile
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

EMPTY_BASE = frozenset({"none", "empty"})


class GitError(Exception):
    pass


def _git(repo: Path, *args: str) -> bytes:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)
    if proc.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {proc.stderr.decode(errors='replace')[-300:]}")
    return proc.stdout


def rev_parse(repo: Path, ref: str) -> str:
    return _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()


def merge_base(repo: Path, a: str, b: str) -> str:
    return _git(repo, "merge-base", a, b).decode().strip()


def first_parent_commits(repo: Path, ref: str, count: int) -> list[str]:
    out = _git(repo, "rev-list", "--first-parent", f"--max-count={count}", ref).decode().split()
    return out


def commit_time(repo: Path, sha: str) -> str:
    """Thời điểm commit (committer date) theo UTC, dạng `YYYY-MM-DDTHH:MM:SSZ` như `started_at`.

    Quy về UTC để so chuỗi với mốc `cutoff` không lệch theo múi giờ của người commit.
    """
    ts = int(_git(repo, "show", "-s", "--format=%ct", sha).decode().strip())
    return dt.datetime.fromtimestamp(ts, dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


_MERGE_PR = re.compile(r"^Merge pull request #(\d+)\b")
_SQUASH_PR = re.compile(r"\(#(\d+)\)\s*$")


def pr_number_from_message(message: str) -> int | None:
    """Số PR từ tiêu đề commit: `Merge pull request #N ...` hoặc `... (#N)` (squash)."""
    title = message.splitlines()[0] if message else ""
    m = _MERGE_PR.match(title) or _SQUASH_PR.search(title)
    return int(m.group(1)) if m else None


def commit_message(repo: Path, sha: str) -> str:
    return _git(repo, "show", "-s", "--format=%B", sha).decode()


def first_pr_commit(repo: Path, base: str, head: str) -> str:
    """Commit đầu tiên trên nhánh PR: phần tử đầu của `base..head` theo thứ tự cũ → mới."""
    out = _git(repo, "rev-list", "--reverse", f"{base}..{head}").decode().split()
    return out[0] if out else head


def parents(repo: Path, sha: str) -> list[str]:
    return _git(repo, "rev-list", "--parents", "-n", "1", sha).decode().split()[1:]


def export_tree(repo: Path, sha: str, dest: Path) -> None:
    data = _git(repo, "archive", "--format=tar", sha)
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=BytesIO(data)) as tf:
        tf.extractall(dest, filter="data")


@dataclass(frozen=True)
class Checkouts:
    head_sha: str
    base_sha: str
    head_dir: Path
    base_dir: Path


@contextmanager
def checkouts(
    repo: Path, base_ref: str, head_ref: str, exact_base: bool = False
) -> Iterator[Checkouts]:
    """`exact_base`: `base_ref` đã là merge-base, không tính lại (kho nông không đủ lịch sử)."""
    head = rev_parse(repo, head_ref)
    empty_base = base_ref in EMPTY_BASE
    if empty_base:
        base = ""
    elif exact_base:
        base = rev_parse(repo, base_ref)
    else:
        base = merge_base(repo, rev_parse(repo, base_ref), head)
    with tempfile.TemporaryDirectory(prefix="pr-triage-co-") as tmp:
        root = Path(tmp)
        export_tree(repo, head, root / "head")
        if empty_base:
            (root / "base").mkdir()
        else:
            export_tree(repo, base, root / "base")
        yield Checkouts(head, base, root / "head", root / "base")
