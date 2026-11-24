"""Chính sách hiển thị (kiến trúc mục 7.2): cách nào được đăng, cảnh báo nào bị thu gọn hoặc ẩn."""

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
    severity_rank,
)


@dataclass(frozen=True)
class DisplayPolicy:
    variant: Variant = Variant.B
    collapse_false: bool = True
    min_severity: str = "low"
    max_findings: int = 1000

    def select(self, findings: Sequence[Finding]) -> tuple[list[Finding], int]:
        """Lọc theo mức độ tối thiểu, sắp giảm dần, cắt theo giới hạn. Trả về (chọn, số bị ẩn)."""
        floor = severity_rank(self.min_severity)
        eligible = [f for f in findings if severity_rank(f.severity) >= floor]
        eligible.sort(
            key=lambda f: (-severity_rank(f.severity), f.file, f.line_start, f.finding_id)
        )
        chosen = eligible[: self.max_findings]
        return chosen, len(findings) - len(chosen)

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
