"""Thông tin diff giữa hai commit: hàm bị đổi, file bị xóa (dùng cho phát hiện "đã sửa")."""

from __future__ import annotations

import re
from pathlib import Path

from pr_triage.context import SymbolIndex
from pr_triage.pipeline.gitrepo import _git

_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.MULTILINE)


def changed_symbols(
    repo: Path, old: str, new: str, new_tree: Path
) -> tuple[set[tuple[str, str | None]], set[str]]:
    """Trả về ({(file, hàm)}, {file bị xóa hoặc đổi tên}) giữa hai commit."""
    status = _git(repo, "diff", "--name-status", "-M", old, new).decode().splitlines()
    removed: set[str] = set()
    for line in status:
        parts = line.split("\t")
        if parts[0].startswith(("D", "R")):
            removed.add(parts[1])
    index = SymbolIndex(new_tree)
    changed: set[tuple[str, str | None]] = set()
    files = [ln.split("\t")[-1] for ln in status if not ln.startswith("D")]
    for file in files:
        patch = _git(repo, "diff", "-U0", old, new, "--", file).decode(errors="replace")
        for m in _HUNK.finditer(patch):
            start, count = int(m.group(1)), int(m.group(2) or "1")
            for line_no in range(start, start + max(count, 1)):
                changed.add((file, index.enclosing_symbol(file, line_no)))
    return changed, removed
