"""Dựng tập cảnh báo duy nhất và tách dev/eval theo thời gian (proposal 7.3)."""

from __future__ import annotations

from collections.abc import Collection

from pr_triage.core.models import PoolEntry, Side
from pr_triage.core.ports import StorePort


def build_pool(
    store: StorePort, cutoff: str, eval_only_repos: Collection[str] = ()
) -> list[PoolEntry]:
    """PR cũ hơn `cutoff` vào dev, mới hơn vào eval. Repo trong `eval_only_repos` luôn vào eval."""
    first: dict[str, PoolEntry] = {}
    for run in store.list_runs():
        for occ in store.list_occurrences(run.run_id):
            if occ.side is not Side.HEAD or not occ.is_new or occ.finding_id in first:
                continue
            is_eval = run.repo_alias in eval_only_repos or run.started_at >= cutoff
            first[occ.finding_id] = PoolEntry(
                occ.finding_id, "eval" if is_eval else "dev", run.run_id, run.repo_alias
            )
    entries = sorted(first.values(), key=lambda e: e.finding_id)
    for e in entries:
        store.save_pool_entry(e)
    return entries
