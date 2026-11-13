"""Lắp pipeline từ tham số: công cụ quét, ngữ cảnh, LLM, kho (ADR 0004)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from pr_triage.context import DataflowProvider, SnippetProvider, load_catalog
from pr_triage.core.models import Finding, RunMode, Variant
from pr_triage.core.ports import ContextPort, LlmPort, ScannerPort
from pr_triage.llm.client import OpenAICompatClient
from pr_triage.llm.config import LlmConfig
from pr_triage.llm.engine import PlainTriageEngine, TriageEngine
from pr_triage.llm.prompt import PROMPT_VERSION
from pr_triage.pipeline.pathglob import make_path_filter
from pr_triage.pipeline.policy import DisplayPolicy
from pr_triage.pipeline.runner import PrPipeline
from pr_triage.scan import SecretScanner, SemgrepAdapter
from pr_triage.store import SqlStore


@dataclass(frozen=True)
class BuildOptions:
    rules: Sequence[str] = field(default_factory=lambda: ["configs/semgrep/java-injection.yml"])
    catalog: str = "configs/context/java.yml"
    db: str = "data/dev/store.sqlite"
    repo_alias: str = "repo"
    mode: RunMode = RunMode.SHADOW
    display: Variant = Variant.B
    engine: str = "graph"
    workers: int = 4
    semgrep_timeout_s: int = 300
    snippet_radius: int = 10
    secrets: bool = True
    min_severity: str = "low"
    max_findings: int = 1000
    path_include: tuple[str, ...] = ()
    path_exclude: tuple[str, ...] = ()


def manifest_hash(opts: BuildOptions, cfg: LlmConfig) -> str:
    h = hashlib.sha256()
    for path in [*opts.rules, opts.catalog]:
        p = Path(path)
        h.update(p.read_bytes() if p.exists() else path.encode())
    h.update(
        f"{cfg.model}|{cfg.temperature}|{cfg.seed}|{opts.display}|{opts.engine}|{PROMPT_VERSION}|r{opts.snippet_radius}|s{opts.secrets}|m{opts.min_severity}|x{opts.max_findings}|{opts.path_include}|{opts.path_exclude}".encode()
    )
    return h.hexdigest()[:16]


def _finding_filter(opts: BuildOptions) -> Callable[[Finding], bool] | None:
    if not (opts.path_include or opts.path_exclude):
        return None
    keep = make_path_filter(opts.path_include, opts.path_exclude)
    return lambda f: keep(f.file)


def build_pipeline(
    opts: BuildOptions, llm: LlmPort | None = None, store: SqlStore | None = None
) -> tuple[PrPipeline, SqlStore]:
    cfg = LlmConfig.from_env()
    store = store or SqlStore(opts.db)
    if llm is None:
        client = OpenAICompatClient(cfg)
        llm = TriageEngine(client) if opts.engine == "graph" else PlainTriageEngine(client)
    contexts: dict[Variant, ContextPort] = {
        Variant.B: SnippetProvider(radius=opts.snippet_radius),
        Variant.C: DataflowProvider(load_catalog(Path(opts.catalog))),
    }
    scanners: list[ScannerPort] = [SemgrepAdapter(opts.rules, timeout_s=opts.semgrep_timeout_s)]
    if opts.secrets:
        scanners.append(SecretScanner())
    pipeline = PrPipeline(
        scanners,
        contexts,
        llm,
        store,
        DisplayPolicy(opts.display, True, opts.min_severity, opts.max_findings),
        repo_alias=opts.repo_alias,
        mode=opts.mode,
        manifest_hash=manifest_hash(opts, cfg),
        workers=opts.workers,
        finding_filter=_finding_filter(opts),
    )
    return pipeline, store
