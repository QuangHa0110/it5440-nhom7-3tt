"""Đăng hoặc cập nhật MỘT comment cho mỗi PR (ADR 0007: job chỉ có quyền comment)."""

from __future__ import annotations

import datetime as dt
import hashlib
from collections.abc import Sequence

from pr_triage.bot.checks import CHECK_NAME, build_check
from pr_triage.bot.render import MARKER, render
from pr_triage.core.models import PostedComment, PrRef, RunMode, TriageResult
from pr_triage.core.ports import ScmPort, StorePort


class Publisher:
    def __init__(self, scm: ScmPort, store: StorePort) -> None:
        self.scm = scm
        self.store = store

    def publish(
        self,
        result: TriageResult,
        pr: PrRef,
        post: bool = False,
        cc: Sequence[str] = (),
        check: bool = False,
    ) -> str | None:
        """Trả về mã comment nếu đã đăng. Chế độ shadow/replay hoặc post=False thì không gọi SCM."""
        body = render(result, cc)
        if not post or result.run.mode is not RunMode.COMMENT:
            return None
        ref = self.scm.upsert_comment(pr, MARKER, body)
        if check:
            title, summary, annotations = build_check(result)
            self.scm.upsert_check(pr, CHECK_NAME, title, summary, annotations)
        self.store.save_comment(
            PostedComment(
                result.run.run_id,
                ref,
                hashlib.sha256(body.encode()).hexdigest(),
                dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
        )
        return ref
