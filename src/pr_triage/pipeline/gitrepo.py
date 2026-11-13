"""Lấy hai bản mã (head và merge-base) từ một repo Git cục bộ, chỉ đọc."""

from __future__ import annotations

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
def checkouts(repo: Path, base_ref: str, head_ref: str) -> Iterator[Checkouts]:
    head = rev_parse(repo, head_ref)
    empty_base = base_ref in EMPTY_BASE
    base = "" if empty_base else merge_base(repo, rev_parse(repo, base_ref), head)
    with tempfile.TemporaryDirectory(prefix="pr-triage-co-") as tmp:
        root = Path(tmp)
        export_tree(repo, head, root / "head")
        if empty_base:
            (root / "base").mkdir()
        else:
            export_tree(repo, base, root / "base")
        yield Checkouts(head, base, root / "head", root / "base")
