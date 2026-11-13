"""Phát hiện cảnh báo đã sửa ở các commit sau lần đăng comment (sơ đồ 8, RQ3)."""

from __future__ import annotations

from pathlib import Path

from pr_triage.bot.states import FixStatus, fix_status
from pr_triage.core.models import TriageResult
from pr_triage.pipeline.diffinfo import changed_symbols
from pr_triage.pipeline.gitrepo import checkouts
from pr_triage.pipeline.runner import PrPipeline


def detect_fixed(
    pipeline: PrPipeline, repo: Path, result: TriageResult, later_ref: str
) -> dict[str, FixStatus]:
    """Trả về trạng thái sửa của từng cảnh báo trong `result` tại commit `later_ref`."""
    with checkouts(repo, result.run.head_sha, later_ref) as co:
        later = {f.fingerprint for f in pipeline._scan(co.head_dir)}
        changed, removed = changed_symbols(repo, result.run.head_sha, co.head_sha, co.head_dir)
    return {
        f.finding_id: fix_status(f.fingerprint, f.file, f.symbol, later, changed, removed)
        for f in result.findings
    }
