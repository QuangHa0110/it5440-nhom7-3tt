"""Chuẩn hóa, gộp trùng và lấy cảnh báo mới (ADR 0011)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from pathlib import Path

from pr_triage.core.fingerprint import FP_VERSION, finding_id, fingerprint, normalize_snippet
from pr_triage.core.models import Finding, RawFinding
from pr_triage.core.secrets import mask

SymbolResolver = Callable[[str, int], str | None]
_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _window(checkout: Path, f: RawFinding, pad: int = 2) -> str:
    try:
        lines = (checkout / f.file).read_text("utf-8", errors="replace").splitlines()
    except OSError:
        return f.snippet
    return "\n".join(lines[max(f.line_start - 1 - pad, 0) : f.line_end + pad])


def to_findings(
    raws: Sequence[RawFinding], checkout: Path, resolve: SymbolResolver
) -> list[Finding]:
    """Gắn dấu vân tay. Cùng (luật, file, hàm, đoạn mã) thì đánh số thứ tự theo vị trí."""
    seen: dict[tuple[str, str, str, str], int] = defaultdict(int)
    out: list[Finding] = []
    for raw in sorted(raws, key=lambda r: (r.file, r.line_start, r.rule_id)):
        symbol = resolve(raw.file, raw.line_start)
        snippet = mask(raw.snippet if symbol else _window(checkout, raw))[0]
        key = (raw.rule_id.lower(), raw.file, symbol or "", normalize_snippet(snippet))
        ordinal = seen[key]
        seen[key] += 1
        fp = fingerprint(raw.rule_id, raw.file, symbol, snippet, ordinal)
        out.append(
            Finding(
                finding_id=finding_id(fp),
                fingerprint=fp,
                fp_version=FP_VERSION,
                tools=(raw.tool,),
                rule_ids=(raw.rule_id,),
                message=raw.message,
                severity=raw.severity,
                file=raw.file,
                line_start=raw.line_start,
                line_end=raw.line_end,
                cwe=raw.cwe,
                symbol=symbol,
                snippet=mask(raw.snippet)[0],
                flow=raw.flow,
                no_symbol=symbol is None,
            )
        )
    return out


def new_findings(head: Sequence[Finding], base: Sequence[Finding]) -> list[Finding]:
    """Cảnh báo mới của PR: dấu vân tay ở head mà base không có."""
    base_fps = {f.fingerprint for f in base}
    return [f for f in head if f.fingerprint not in base_fps]


def _overlap(a: Finding, b: Finding) -> bool:
    return a.line_start <= b.line_end and b.line_start <= a.line_end


def deduplicate(findings: Sequence[Finding]) -> list[Finding]:
    """Gộp cảnh báo cùng CWE, file, hàm có vùng chồng nhau thành một cảnh báo nhiều nguồn."""
    groups: list[list[Finding]] = []
    for f in sorted(findings, key=lambda x: (x.file, x.line_start, x.fingerprint)):
        placed = False
        if f.cwe is not None:
            for g in groups:
                head = g[0]
                if (head.cwe, head.file, head.symbol) == (f.cwe, f.file, f.symbol) and any(
                    _overlap(m, f) for m in g
                ):
                    g.append(f)
                    placed = True
                    break
        if not placed:
            groups.append([f])
    return [_merge(g) for g in groups]


def _merge(group: list[Finding]) -> Finding:
    if len(group) == 1:
        return group[0]
    primary = min(group, key=lambda f: f.fingerprint)
    top = max(group, key=lambda f: _SEVERITY_RANK.get(f.severity, 1))
    flow = next((f.flow for f in group if f.flow), ())
    return Finding(
        **{
            **primary.__dict__,
            "tools": tuple(sorted({t for f in group for t in f.tools})),
            "rule_ids": tuple(sorted({r for f in group for r in f.rule_ids})),
            "severity": top.severity,
            "line_start": min(f.line_start for f in group),
            "line_end": max(f.line_end for f in group),
            "flow": flow,
        }
    )
