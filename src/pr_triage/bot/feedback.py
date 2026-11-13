"""Thu phản hồi từ SCM: trả lời fp/tp theo cảnh báo, phản ứng, commit, trạng thái PR (ADR 0010)."""

from __future__ import annotations

import re

from pr_triage.core.alias import Aliaser
from pr_triage.core.models import FeedbackEvent, FeedbackKind, PrRef, TriageResult
from pr_triage.core.ports import ScmPort, StorePort

_REPLY = re.compile(r"(?im)^\s*(fp|tp)\s+([0-9a-f]{6,12})\b[ \t]*(.*)$")


class FeedbackCollector:
    def __init__(self, scm: ScmPort, store: StorePort, aliaser: Aliaser) -> None:
        self.scm = scm
        self.store = store
        self.aliaser = aliaser

    def collect(self, result: TriageResult, pr: PrRef, comment_ref: str) -> list[FeedbackEvent]:
        """Trả về các sự kiện MỚI đã được ghi vào kho (chỉ thêm, không sửa)."""
        run_id = result.run.run_id
        by_code = {d.short_code: d.finding_id for d in result.displayed}
        known = {self._key(e) for e in self.store.list_feedback(run_id)}
        found: list[FeedbackEvent] = []
        for reply in self.scm.list_replies(pr, comment_ref):
            actor = self.aliaser.alias("user", reply.author)
            for m in _REPLY.finditer(reply.body):
                kind = (
                    FeedbackKind.REPLY_FP if m.group(1).lower() == "fp" else FeedbackKind.REPLY_TP
                )
                fid = by_code.get(m.group(2).lower()[:6]) or by_code.get(m.group(2).lower())
                if fid is None:
                    continue
                found.append(FeedbackEvent(run_id, fid, kind, actor, reply.at, m.group(3).strip()))
        for r in self.scm.list_reactions(pr, comment_ref):
            found.append(
                FeedbackEvent(
                    run_id,
                    None,
                    FeedbackKind.REACTION,
                    self.aliaser.alias("user", r.author),
                    r.at,
                    r.content,
                )
            )
        for sha in self.scm.list_commits(pr):
            if sha != result.run.head_sha:
                found.append(FeedbackEvent(run_id, None, FeedbackKind.COMMIT, "", "", sha))
        state = self.scm.pr_state(pr)
        if state == "merged":
            found.append(FeedbackEvent(run_id, None, FeedbackKind.MERGE, "", "", state))
        elif state == "closed":
            found.append(FeedbackEvent(run_id, None, FeedbackKind.CLOSE, "", "", state))
        fresh = []
        for e in found:
            if self._key(e) in known:
                continue
            known.add(self._key(e))
            self.store.add_feedback(e)
            fresh.append(e)
        return fresh

    @staticmethod
    def _key(e: FeedbackEvent) -> tuple[str, str | None, str, str, str]:
        return (e.kind.value, e.finding_id, e.actor_alias, e.at, e.value)
