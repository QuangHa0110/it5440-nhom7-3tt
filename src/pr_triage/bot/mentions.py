"""Danh sách CC người liên quan (ADR 0014 D3, D5). Chỉ từ nguồn tin cậy, không từ mô hình."""

from __future__ import annotations

import re
from collections.abc import Callable, Collection, Sequence

from pr_triage.core.models import ShownAs, TriageResult, severity_rank

_HANDLE = re.compile(r"^@[A-Za-z0-9][A-Za-z0-9-]{0,38}(/[A-Za-z0-9_.-]{1,100})?$")
MAX_CC = 10


def compute_cc(
    result: TriageResult,
    modes: Collection[str],
    min_severity: str,
    author: str = "",
    users: Sequence[str] = (),
    owners_of: Callable[[list[str]], list[str]] | None = None,
    exclude: Collection[str] = (),
) -> list[str]:
    """CC chỉ khi có cảnh báo hiển thị mở từ mức `min_severity`."""
    if not modes or set(modes) == {"none"}:
        return []
    by_id = {f.finding_id: f for f in result.findings}
    floor = severity_rank(min_severity)
    hot = [
        by_id[d.finding_id]
        for d in result.displayed
        if d.shown_as is ShownAs.EXPANDED
        and d.finding_id in by_id
        and severity_rank(by_id[d.finding_id].severity) >= floor
    ]
    if not hot:
        return []
    out: list[str] = []
    if "author" in modes and author:
        out.append(author if author.startswith("@") else f"@{author}")
    if "codeowners" in modes and owners_of is not None:
        out.extend(owners_of([f.file for f in hot]))
    if "list" in modes:
        out.extend(users)
    blocked = {e.lower() for e in exclude}
    seen: list[str] = []
    for h in out:
        if _HANDLE.match(h) and h.lower() not in blocked and h not in seen:
            seen.append(h)
    return seen[:MAX_CC]
