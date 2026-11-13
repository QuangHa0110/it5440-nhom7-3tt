"""Lắp pipeline từ tham số: công cụ quét, ngữ cảnh, LLM, kho (ADR 0004)."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from pr_triage.context import DataflowProvider, SnippetProvider, load_catalog
from pr_triage.core.models import RunMode, Variant
from pr_triage.core.ports import ContextPort, LlmPort
from pr_triage.llm.client import OpenAICompatClient
from pr_triage.llm.config import LlmConfig
from pr_triage.llm.engine import PlainTriageEngine, TriageEngine
from pr_triage.llm.prompt import PROMPT_VERSION
from pr_triage.pipeline.policy import DisplayPolicy
from pr_triage.pipeline.runner import PrPipeline
from pr_triage.scan import SemgrepAdapter
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


def manifest_hash(opts: BuildOptions, cfg: LlmConfig) -> str:
    h = hashlib.sha256()
    for path in [*opts.rules, opts.catalog]:
        p = Path(path)
        h.update(p.read_bytes() if p.exists() else path.encode())
    h.update(
        f"{cfg.model}|{cfg.temperature}|{cfg.seed}|{opts.display}|{opts.engine}|{PROMPT_VERSION}|r{opts.snippet_radius}".encode()
    )
    return h.hexdigest()[:16]


def build_pipeline(opts: BuildOptions, llm: LlmPort | None = None) -> tuple[PrPipeline, SqlStore]:
    cfg = LlmConfig.from_env()
    store = SqlStore(opts.db)
    if llm is None:
        client = OpenAICompatClient(cfg)
        llm = TriageEngine(client) if opts.engine == "graph" else PlainTriageEngine(client)
    contexts: dict[Variant, ContextPort] = {
        Variant.B: SnippetProvider(radius=opts.snippet_radius),
        Variant.C: DataflowProvider(load_catalog(Path(opts.catalog))),
    }
    pipeline = PrPipeline(
        [SemgrepAdapter(opts.rules, timeout_s=opts.semgrep_timeout_s)],
        contexts,
        llm,
        store,
        DisplayPolicy(opts.display),
        repo_alias=opts.repo_alias,
        mode=opts.mode,
        manifest_hash=manifest_hash(opts, cfg),
        workers=opts.workers,
    )
    return pipeline, store
