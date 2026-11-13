"""Chính sách hiển thị (kiến trúc mục 7.2): cách nào được đăng, cảnh báo nào bị thu gọn."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from pr_triage.core.models import (
    DisplayedAlert,
    Finding,
    ShownAs,
    Variant,
    Verdict,
    VerdictLabel,
)


@dataclass(frozen=True)
class DisplayPolicy:
    variant: Variant = Variant.B
    collapse_false: bool = True

    def decide(
        self, run_id: str, findings: Sequence[Finding], verdicts: Sequence[Verdict]
    ) -> list[DisplayedAlert]:
        by_key = {(v.finding_id, v.variant): v for v in verdicts}
        codes = short_codes([f.finding_id for f in findings])
        out: list[DisplayedAlert] = []
        for f in findings:
            v = by_key.get((f.finding_id, self.variant))
            collapse = (
                self.collapse_false
                and self.variant is not Variant.A
                and v is not None
                and v.label is VerdictLabel.LIKELY_FALSE
                and v.error is None
            )
            out.append(
                DisplayedAlert(
                    run_id=run_id,
                    finding_id=f.finding_id,
                    shown_as=ShownAs.COLLAPSED if collapse else ShownAs.EXPANDED,
                    displayed_variant=self.variant,
                    short_code=codes[f.finding_id],
                )
            )
        return out


def short_codes(ids: Sequence[str]) -> dict[str, str]:
    """Mã ngắn không trùng trong một PR (ADR 0010 D1)."""
    for width in range(6, 13):
        codes = {i: i[:width] for i in ids}
        if len(set(codes.values())) == len(codes):
            return codes
    return {i: i for i in ids}
