"""Chuyển trạng thái của cảnh báo đã hiển thị (sơ đồ 8, số đo của RQ3)."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import replace
from enum import StrEnum

from pr_triage.core.models import AlertState, DisplayedAlert, FeedbackEvent, FeedbackKind


class FixStatus(StrEnum):
    PRESENT = "present"
    FIXED = "fixed"
    VANISHED_NOT_FIXED = "vanished_not_fixed"


def fix_status(
    fingerprint: str,
    file: str,
    symbol: str | None,
    later_fingerprints: Collection[str],
    changed_symbols: Collection[tuple[str, str | None]],
    removed_files: Collection[str],
) -> FixStatus:
    """Đã sửa khi dấu vân tay biến mất VÀ hàm chứa cảnh báo có trong diff. File bị xóa thì không."""
    if fingerprint in later_fingerprints:
        return FixStatus.PRESENT
    if file in removed_files:
        return FixStatus.VANISHED_NOT_FIXED
    return FixStatus.FIXED if (file, symbol) in changed_symbols else FixStatus.VANISHED_NOT_FIXED


def resolve_states(
    alerts: Sequence[DisplayedAlert],
    events: Sequence[FeedbackEvent],
    fixed_ids: Collection[str] = (),
    closed: bool = False,
    trusted_roles: Collection[str] | None = None,
) -> list[DisplayedAlert]:
    """`trusted_roles`: chỉ `fp` của các vai trò này làm MARKED_FALSE (ADR 0014 D2)."""
    out: list[DisplayedAlert] = []
    for a in alerts:
        mine = [e for e in events if e.finding_id == a.finding_id]
        kinds = {e.kind for e in mine}
        if trusted_roles is not None and FeedbackKind.REPLY_FP in kinds:
            trusted = any(
                e.kind is FeedbackKind.REPLY_FP and e.actor_role in trusted_roles for e in mine
            )
            if not trusted:
                kinds = (kinds - {FeedbackKind.REPLY_FP}) | {FeedbackKind.REPLY_TP}
        if a.finding_id in fixed_ids:
            state = AlertState.FIXED
        elif FeedbackKind.REPLY_FP in kinds:
            state = AlertState.MARKED_FALSE
        elif kinds & {FeedbackKind.REPLY_TP, FeedbackKind.REACTION}:
            state = AlertState.RESPONDED
        elif closed:
            state = AlertState.IGNORED
        else:
            state = AlertState.SHOWN
        out.append(replace(a, state=state))
    return out
