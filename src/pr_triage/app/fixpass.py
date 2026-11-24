"""Đánh dấu cảnh báo đã sửa khi PR có commit mới (sơ đồ 8, RQ3)."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

from pr_triage.bot.states import FixStatus, fix_status
from pr_triage.core.models import AlertState, PrRun, Side
from pr_triage.pipeline.diffinfo import changed_symbols
from pr_triage.pipeline.gitrepo import export_tree
from pr_triage.store import SqlStore


def mark_fixed(store: SqlStore, repo: Path, prev: PrRun, new: PrRun) -> int:
    """So lượt chạy trước với lượt mới của cùng PR. Trả về số cảnh báo được đánh dấu đã sửa."""
    later = {
        f.fingerprint
        for o in store.list_occurrences(new.run_id)
        if o.side is Side.HEAD and (f := store.get_finding(o.finding_id)) is not None
    }
    with tempfile.TemporaryDirectory(prefix="pr-triage-fix-") as tmp:
        tree = Path(tmp)
        export_tree(repo, new.head_sha, tree)
        changed, removed = changed_symbols(repo, prev.head_sha, new.head_sha, tree)
    n = 0
    for alert in store.list_displayed(prev.run_id):
        if alert.state not in (AlertState.SHOWN, AlertState.RESPONDED):
            continue
        f = store.get_finding(alert.finding_id)
        if f is None:
            continue
        if fix_status(f.fingerprint, f.file, f.symbol, later, changed, removed) is FixStatus.FIXED:
            store.save_displayed(replace(alert, state=AlertState.FIXED))
            n += 1
    return n
