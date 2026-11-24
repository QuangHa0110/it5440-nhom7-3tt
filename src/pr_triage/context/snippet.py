"""Cách B: vài dòng mã quanh vị trí báo."""

from __future__ import annotations

import time
from pathlib import Path

from pr_triage.context.bundle import make_bundle
from pr_triage.core.errors import ContextError
from pr_triage.core.models import ContextBundle, ContextSlice, Finding, Variant


def read_lines(checkout: Path, rel: str, start: int, end: int) -> tuple[int, int, str]:
    try:
        lines = (checkout / rel).read_text("utf-8", errors="replace").splitlines()
    except OSError as exc:
        raise ContextError(f"không đọc được {rel}: {exc}") from exc
    s = max(start, 1)
    e = min(end, len(lines))
    return s, e, "\n".join(lines[s - 1 : e])


class SnippetProvider:
    variant = Variant.B

    def __init__(self, radius: int = 10) -> None:
        self._radius = radius

    def extract(self, finding: Finding, checkout: Path) -> ContextBundle:
        t0 = time.monotonic()
        s, e, text = read_lines(
            checkout,
            finding.file,
            finding.line_start - self._radius,
            finding.line_end + self._radius,
        )
        sl = ContextSlice(finding.file, s, e, "alert-site", text)
        return make_bundle(
            Variant.B, finding.finding_id, [sl], extract_ms=int((time.monotonic() - t0) * 1000)
        )
