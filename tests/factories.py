"""Hàm dựng đối tượng miền cho test."""

from pr_triage.core.fingerprint import finding_id, fingerprint
from pr_triage.core.models import (
    ContextBundle,
    ContextSlice,
    EvidenceItem,
    Finding,
    PrRun,
    RunMode,
    RunStatus,
    Variant,
    Verdict,
    VerdictLabel,
)


def make_finding(
    rule: str = "java.sqli",
    path: str = "src/OrderDao.java",
    snippet: str = 'stmt.executeQuery("SELECT * FROM t WHERE id=" + id)',
    symbol: str | None = "OrderDao.find",
    ordinal: int = 0,
    line: int = 42,
) -> Finding:
    fp = fingerprint(rule, path, symbol, snippet, ordinal)
    return Finding(
        finding_id=finding_id(fp),
        fingerprint=fp,
        fp_version=1,
        tools=("semgrep",),
        rule_ids=(rule,),
        message="SQL injection",
        severity="high",
        file=path,
        line_start=line,
        line_end=line,
        cwe="CWE-89",
        symbol=symbol,
        snippet=snippet,
    )


def make_bundle(f: Finding, variant: Variant = Variant.B) -> ContextBundle:
    return ContextBundle(
        bundle_hash="b" * 64,
        variant=variant,
        finding_id=f.finding_id,
        slices=(ContextSlice(f.file, 40, 44, "sink", "code"),),
        sink="sql-query",
        missing=("callers: mơ hồ",),
    )


def make_verdict(f: Finding, variant: Variant = Variant.B) -> Verdict:
    return Verdict(
        verdict_id=f"{f.finding_id}-{variant.value}",
        finding_id=f.finding_id,
        variant=variant,
        model_id="m",
        prompt_version="p1",
        label=VerdictLabel.LIKELY_TRUE,
        explanation="x",
        evidence=(EvidenceItem(f.file, 42, "nối chuỗi"),),
        tokens_in=10,
        tokens_out=5,
    )


def make_run(run_id: str = "r1") -> PrRun:
    return PrRun(
        run_id=run_id,
        repo_alias="repo-1",
        pr_number=7,
        head_sha="h",
        base_sha="b",
        mode=RunMode.SHADOW,
        status=RunStatus.OK,
        started_at="2026-11-13T00:00:00Z",
        notes=("n",),
    )
