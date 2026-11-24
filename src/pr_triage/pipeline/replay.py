"""Chọn cặp base/head và số PR cho từng commit khi chạy lại lịch sử (`pr-triage replay`)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pr_triage.pipeline.gitrepo import (
    commit_message,
    first_parent_commits,
    first_pr_commit,
    parents,
    pr_number_from_message,
)

Side = Literal["merged", "first"]


@dataclass(frozen=True)
class ReplayItem:
    sha: str
    base: str
    head: str
    pr_number: int
    skip_reason: str | None = None


def plan_replay(repo: Path, ref: str, count: int, side: Side = "merged") -> list[ReplayItem]:
    """Một mục cho mỗi commit first-parent của `ref`.

    - Merge commit: base là parent đầu, head là đỉnh nhánh PR (`merged`) hoặc commit đầu
      của nhánh PR (`first`, dùng làm mốc RQ3).
    - Squash hoặc commit thẳng: base là parent, head là chính commit; không có `first`.
    - Số PR lấy từ tiêu đề commit; commit không gắn PR nhận số âm `-i` để không trùng số thật.
    """
    items: list[ReplayItem] = []
    for i, sha in enumerate(first_parent_commits(repo, ref, count), 1):
        number = pr_number_from_message(commit_message(repo, sha)) or -i
        ps = parents(repo, sha)
        if not ps:
            items.append(ReplayItem(sha, sha, sha, number, "commit gốc, không có parent"))
            continue
        if len(ps) > 1:
            head = first_pr_commit(repo, ps[0], ps[1]) if side == "first" else ps[1]
            items.append(ReplayItem(sha, ps[0], head, number))
        elif side == "first":
            items.append(
                ReplayItem(sha, ps[0], sha, number, "không phải merge commit, không có commit đầu")
            )
        else:
            items.append(ReplayItem(sha, ps[0], sha, number))
    return items
