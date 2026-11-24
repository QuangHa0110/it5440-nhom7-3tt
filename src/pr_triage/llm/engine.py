"""Máy nhận định: một đồ thị hữu hạn, mỗi nút tất định trừ nút gọi mô hình (ADR 0003, 0009).

`PlainTriageEngine` là hàm Python thuần. `TriageEngine` cùng các bước nhưng chạy trên LangGraph.
Hai bản phải cho kết quả trùng nhau trên cùng đầu vào.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Any, Protocol, TypedDict

from langgraph.graph import END, StateGraph

from pr_triage.core.errors import LlmError
from pr_triage.core.models import ContextBundle, Finding, Variant, Verdict, VerdictLabel
from pr_triage.llm.budget import BudgetGuard
from pr_triage.llm.cache import VerdictCache, cache_key
from pr_triage.llm.client import ChatResult
from pr_triage.llm.config import LlmConfig
from pr_triage.llm.prompt import PROMPT_VERSION, build_messages, repair_message
from pr_triage.llm.redact import redact
from pr_triage.llm.schema import VerdictFormatError, validate_verdict

MAX_CALLS = 2


class ChatClient(Protocol):
    @property
    def config(self) -> LlmConfig: ...

    def chat(self, messages: list[dict[str, str]]) -> ChatResult: ...


class TriageState(TypedDict, total=False):
    finding: Finding
    bundle: ContextBundle
    key: str
    messages: list[dict[str, str]]
    result: ChatResult | None
    attempts: int
    tokens_in: int
    tokens_out: int
    latency_ms: int
    last_error: str
    verdict: Verdict


def _redact_bundle(bundle: ContextBundle) -> ContextBundle:
    from dataclasses import replace

    slices = tuple(replace(s, text=redact(s.text)[0]) for s in bundle.slices)
    return replace(bundle, slices=slices)


class TriageSteps:
    """Các nút của đồ thị, dùng chung cho hai bản hiện thực."""

    def __init__(
        self,
        client: ChatClient,
        cache: VerdictCache | None = None,
        budget: BudgetGuard | None = None,
    ) -> None:
        self.client = client
        self.cache = cache or VerdictCache()
        self.budget = budget or BudgetGuard()

    def _verdict(self, state: TriageState, label: VerdictLabel, **kw: Any) -> Verdict:
        f, b = state["finding"], state["bundle"]
        cfg = self.client.config
        vid = hashlib.sha256(
            f"{f.finding_id}{b.variant}{b.bundle_hash}{cfg.model}".encode()
        ).hexdigest()[:12]
        return Verdict(
            verdict_id=f"{f.finding_id}-{b.variant.value}-{vid}",
            finding_id=f.finding_id,
            variant=b.variant,
            model_id=cfg.model,
            prompt_version=PROMPT_VERSION,
            label=label,
            tokens_in=state.get("tokens_in", 0),
            tokens_out=state.get("tokens_out", 0),
            latency_ms=state.get("latency_ms", 0),
            **kw,
        )

    def lookup_cache(self, state: TriageState) -> TriageState:
        f, b, cfg = state["finding"], state["bundle"], self.client.config
        key = cache_key(
            f.fingerprint,
            b.bundle_hash,
            PROMPT_VERSION,
            cfg.model,
            {"t": cfg.temperature, "seed": cfg.seed, "max": cfg.max_tokens},
        )
        hit = self.cache.get(key)
        out: TriageState = {"key": key, "attempts": 0}
        if hit is not None:
            from dataclasses import replace

            out["verdict"] = replace(hit, cached=True, tokens_in=0, tokens_out=0, latency_ms=0)
        return out

    def check_budget(self, state: TriageState) -> TriageState:
        if self.budget.allowed():
            return {}
        return {"verdict": self._verdict(state, VerdictLabel.UNKNOWN, error="budget")}

    def build_prompt(self, state: TriageState) -> TriageState:
        redacted = _redact_bundle(state["bundle"])
        return {"messages": build_messages(state["finding"], redacted)}

    def call_model(self, state: TriageState) -> TriageState:
        attempts = state.get("attempts", 0) + 1
        msgs = list(state["messages"])
        if state.get("last_error") and state.get("result") is not None:
            msgs += [
                {"role": "assistant", "content": state["result"].text},  # type: ignore[union-attr]
                repair_message(state["last_error"]),
            ]
        try:
            res = self.client.chat(msgs)
        except LlmError as exc:
            return {
                "attempts": MAX_CALLS,
                "result": None,
                "verdict": self._verdict(state, VerdictLabel.UNKNOWN, error=f"llm_error: {exc}"),
            }
        self.budget.record(res.tokens_in + res.tokens_out)
        return {
            "attempts": attempts,
            "result": res,
            "tokens_in": state.get("tokens_in", 0) + res.tokens_in,
            "tokens_out": state.get("tokens_out", 0) + res.tokens_out,
            "latency_ms": state.get("latency_ms", 0) + res.latency_ms,
        }

    def validate(self, state: TriageState) -> TriageState:
        res = state["result"]
        assert res is not None
        try:
            if res.finish_reason == "length":
                raise VerdictFormatError("đầu ra bị cắt cụt (finish_reason=length)")
            parsed = validate_verdict(res.text, state["bundle"], state["finding"].finding_id)
        except VerdictFormatError as exc:
            if state["attempts"] < MAX_CALLS:
                return {"last_error": str(exc)}
            return {
                "last_error": str(exc),
                "verdict": self._verdict(state, VerdictLabel.INVALID, error=str(exc)),
            }
        v = self._verdict(
            state,
            parsed.label,
            explanation=parsed.explanation,
            evidence=parsed.evidence,
            missing_context=parsed.missing_context,
        )
        return {"verdict": v, "last_error": ""}

    def store(self, state: TriageState) -> TriageState:
        v = state["verdict"]
        if v.error is None and not v.cached and v.label is not VerdictLabel.INVALID:
            self.cache.put(state["key"], v)
        return {}


class PlainTriageEngine:
    def __init__(
        self,
        client: ChatClient,
        cache: VerdictCache | None = None,
        budget: BudgetGuard | None = None,
    ) -> None:
        self.steps = TriageSteps(client, cache, budget)

    def triage(self, finding: Finding, bundle: ContextBundle) -> Verdict:
        st: TriageState = {"finding": finding, "bundle": bundle}
        s = self.steps
        st.update(s.lookup_cache(st))
        if "verdict" not in st:
            st.update(s.check_budget(st))
        if "verdict" not in st:
            st.update(s.build_prompt(st))
            while "verdict" not in st:
                st.update(s.call_model(st))
                if "verdict" in st:
                    break
                st.update(s.validate(st))
        st.update(s.store(st))
        return st["verdict"]


class TriageEngine:
    """Đồ thị LangGraph: DAG cộng đúng một cạnh lùi có trần (ADR 0009 D3)."""

    def __init__(
        self,
        client: ChatClient,
        cache: VerdictCache | None = None,
        budget: BudgetGuard | None = None,
    ) -> None:
        self.steps = TriageSteps(client, cache, budget)
        self._graph = self._build()

    def _build(self) -> Any:
        s = self.steps
        g: StateGraph[TriageState] = StateGraph(TriageState)
        g.add_node("lookup_cache", s.lookup_cache)
        g.add_node("check_budget", s.check_budget)
        g.add_node("build_prompt", s.build_prompt)
        g.add_node("call_model", s.call_model)
        g.add_node("validate", s.validate)
        g.add_node("store", s.store)
        g.set_entry_point("lookup_cache")
        done: Callable[[TriageState], bool] = lambda st: "verdict" in st  # noqa: E731
        g.add_conditional_edges(
            "lookup_cache",
            lambda st: "store" if done(st) else "check_budget",
            {"store": "store", "check_budget": "check_budget"},
        )
        g.add_conditional_edges(
            "check_budget",
            lambda st: "store" if done(st) else "build_prompt",
            {"store": "store", "build_prompt": "build_prompt"},
        )
        g.add_edge("build_prompt", "call_model")
        g.add_conditional_edges(
            "call_model",
            lambda st: "store" if done(st) else "validate",
            {"store": "store", "validate": "validate"},
        )
        g.add_conditional_edges(
            "validate",
            lambda st: "store" if done(st) else "call_model",
            {"store": "store", "call_model": "call_model"},
        )
        g.add_edge("store", END)
        return g.compile()

    def triage(self, finding: Finding, bundle: ContextBundle) -> Verdict:
        out = self._graph.invoke({"finding": finding, "bundle": bundle})
        verdict: Verdict = out["verdict"]
        return verdict


__all__ = ["PlainTriageEngine", "TriageEngine", "Variant"]
