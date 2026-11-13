"""PrPipeline: một lượt chạy trên một PR (sơ đồ 4, kiến trúc mục 7)."""

from __future__ import annotations

import datetime as dt
import hashlib
import logging
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

from pr_triage.context import SymbolIndex
from pr_triage.core.errors import ContextError, ScanError
from pr_triage.core.models import (
    ContextBundle,
    Finding,
    Occurrence,
    PrRun,
    RawFinding,
    RunMode,
    RunStatus,
    Side,
    TriageResult,
    Variant,
    Verdict,
    VerdictLabel,
)
from pr_triage.core.ports import ContextPort, LlmPort, ScannerPort, StorePort
from pr_triage.normalize import deduplicate, new_findings, to_findings
from pr_triage.pipeline.gitrepo import Checkouts, checkouts
from pr_triage.pipeline.policy import DisplayPolicy

log = logging.getLogger("pr_triage.pipeline")

SymbolFactory = Callable[[Path], Callable[[str, int], str | None]]


def _default_symbols(root: Path) -> Callable[[str, int], str | None]:
    return SymbolIndex(root).enclosing_symbol


def _now() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def formal_verdict_a(f: Finding) -> Verdict:
    """Cách A không dùng LLM: coi mọi cảnh báo là likely_true để so trên cùng một bảng."""
    return Verdict(
        verdict_id=f"{f.finding_id}-A",
        finding_id=f.finding_id,
        variant=Variant.A,
        model_id="none",
        prompt_version="none",
        label=VerdictLabel.LIKELY_TRUE,
        explanation="Cảnh báo của công cụ quét, chưa qua LLM.",
    )


class PrPipeline:
    def __init__(
        self,
        scanners: Sequence[ScannerPort],
        contexts: dict[Variant, ContextPort],
        llm: LlmPort,
        store: StorePort,
        policy: DisplayPolicy | None = None,
        repo_alias: str = "repo",
        mode: RunMode = RunMode.SHADOW,
        manifest_hash: str = "",
        workers: int = 4,
        symbols: SymbolFactory = _default_symbols,
        finding_filter: Callable[[Finding], bool] | None = None,
    ) -> None:
        self.scanners = list(scanners)
        self.contexts = contexts
        self.llm = llm
        self.store = store
        self.policy = policy or DisplayPolicy()
        self.repo_alias = repo_alias
        self.mode = mode
        self.manifest_hash = manifest_hash
        self.workers = workers
        self.symbols = symbols
        self.finding_filter = finding_filter

    def _scan(self, root: Path) -> list[Finding]:
        raws: list[RawFinding] = []
        for scanner in self.scanners:
            raws.extend(scanner.scan(root))
        found = to_findings(raws, root, self.symbols(root))
        keep = self.finding_filter
        return [f for f in found if keep(f)] if keep else found

    def _bundle(self, port: ContextPort, f: Finding, root: Path, notes: list[str]) -> ContextBundle:
        try:
            return port.extract(f, root)
        except ContextError as exc:
            notes.append(f"{f.finding_id}: ngữ cảnh {port.variant.value} lỗi: {exc}")
            fallback = self.contexts.get(Variant.B)
            if fallback is None or fallback is port:
                raise
            b = fallback.extract(f, root)
            return replace(
                b, variant=port.variant, missing=(*b.missing, f"dùng ngữ cảnh B vì lỗi: {exc}")
            )

    def run(
        self,
        repo: Path,
        base_ref: str,
        head_ref: str,
        pr_number: int,
        exact_base: bool = False,
    ) -> TriageResult:
        t0 = time.monotonic()
        with checkouts(repo, base_ref, head_ref, exact_base) as co:
            run_id = hashlib.sha256(
                f"{self.repo_alias}{pr_number}{co.head_sha}{self.mode}{time.time_ns()}".encode()
            ).hexdigest()[:12]
            run = PrRun(
                run_id,
                self.repo_alias,
                pr_number,
                co.head_sha,
                co.base_sha,
                self.mode,
                RunStatus.OK,
                _now(),
                manifest_hash=self.manifest_hash,
            )
            try:
                result = self._run(run, co)
            except ScanError as exc:
                failed = replace(run, status=RunStatus.FAILED, notes=(f"quét lỗi: {exc}",))
                result = TriageResult(failed, errors=(f"quét lỗi: {exc}",))
            run = replace(
                result.run, duration_s=round(time.monotonic() - t0, 3), started_at=run.started_at
            )
            result = replace(result, run=run)
            self.store.save_run(run)
            return result

    def _run(self, run: PrRun, co: Checkouts) -> TriageResult:
        head_all = self._scan(co.head_dir)
        base_all = self._scan(co.base_dir)
        fresh = new_findings(head_all, base_all)
        new_ids = {f.finding_id for f in fresh}
        merged = deduplicate(fresh)
        for f in head_all:
            self.store.upsert_finding(f)
            self.store.add_occurrence(
                Occurrence(
                    run.run_id,
                    f.finding_id,
                    Side.HEAD,
                    f.line_start,
                    f.line_end,
                    f.tools[0],
                    f.finding_id in new_ids,
                )
            )
        for f in base_all:
            self.store.upsert_finding(f)
            self.store.add_occurrence(
                Occurrence(
                    run.run_id, f.finding_id, Side.BASE, f.line_start, f.line_end, f.tools[0], False
                )
            )
        notes: list[str] = []
        verdicts = [formal_verdict_a(f) for f in merged]
        jobs = [(f, v) for f in merged for v in (Variant.B, Variant.C) if v in self.contexts]

        def work(job: tuple[Finding, Variant]) -> tuple[ContextBundle | None, Verdict, list[str]]:
            f, variant = job
            local: list[str] = []
            try:
                bundle = self._bundle(self.contexts[variant], f, co.head_dir, local)
            except ContextError as exc:
                local.append(f"{f.finding_id}: không trích được ngữ cảnh {variant.value}: {exc}")
                v = Verdict(
                    f"{f.finding_id}-{variant.value}-ctx",
                    f.finding_id,
                    variant,
                    "none",
                    "none",
                    VerdictLabel.UNKNOWN,
                    error=f"context_error: {exc}",
                )
                return None, v, local
            self.store.save_bundle(bundle)
            return bundle, self.llm.triage(f, bundle), local

        with ThreadPoolExecutor(max_workers=max(self.workers, 1)) as ex:
            for _, verdict, local in ex.map(work, jobs):
                verdicts.append(verdict)
                notes.extend(local)
        for v in verdicts:
            self.store.save_verdict(run.run_id, v)
        shown, hidden = self.policy.select(merged)
        if hidden:
            notes.append(f"ẩn: {hidden} cảnh báo dưới ngưỡng mức độ hoặc vượt giới hạn số cảnh báo")
        displayed = self.policy.decide(run.run_id, shown, verdicts)
        for d in displayed:
            self.store.save_displayed(d)
        errors = tuple(n for n in notes if not n.startswith("ẩn:")) + tuple(
            f"{v.finding_id}/{v.variant.value}: {v.error}" for v in verdicts if v.error
        )
        status = RunStatus.DEGRADED if errors else RunStatus.OK
        return TriageResult(
            run=replace(run, status=status, notes=tuple(notes)),
            findings=tuple(merged),
            verdicts=tuple(verdicts),
            displayed=tuple(displayed),
            errors=errors,
        )
