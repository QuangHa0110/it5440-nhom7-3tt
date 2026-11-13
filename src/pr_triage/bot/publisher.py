"""Đăng hoặc cập nhật MỘT comment cho mỗi PR (ADR 0007: job chỉ có quyền comment)."""

from __future__ import annotations

import datetime as dt
import hashlib

from pr_triage.bot.render import MARKER, render
from pr_triage.core.models import PostedComment, PrRef, RunMode, TriageResult
from pr_triage.core.ports import ScmPort, StorePort


class Publisher:
    def __init__(self, scm: ScmPort, store: StorePort) -> None:
        self.scm = scm
        self.store = store

    def publish(self, result: TriageResult, pr: PrRef, post: bool = False) -> str | None:
        """Trả về mã comment nếu đã đăng. Chế độ shadow/replay hoặc post=False thì không gọi SCM."""
        body = render(result)
        if not post or result.run.mode is not RunMode.COMMENT:
            return None
        ref = self.scm.upsert_comment(pr, MARKER, body)
        self.store.save_comment(
            PostedComment(
                result.run.run_id,
                ref,
                hashlib.sha256(body.encode()).hexdigest(),
                dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
        )
        return ref
