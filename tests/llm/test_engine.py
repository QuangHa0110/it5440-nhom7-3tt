import json

import pytest

from pr_triage.core.errors import LlmError
from pr_triage.core.models import Variant, VerdictLabel
from pr_triage.core.ports import LlmPort
from pr_triage.llm.budget import BudgetGuard
from pr_triage.llm.cache import VerdictCache
from pr_triage.llm.engine import PlainTriageEngine, TriageEngine
from tests.factories import make_bundle, make_finding
from tests.llm.fakes_llm import ScriptedClient

F = make_finding()
B = make_bundle(F, Variant.B)
GOOD = json.dumps(
    {
        "label": "likely_true",
        "explanation": "ok",
        "evidence": [{"file": F.file, "line": 42}],
        "missing_context": [],
    }
)

ENGINES = [PlainTriageEngine, TriageEngine]


@pytest.fixture(params=ENGINES, ids=["plain", "langgraph"])
def engine_cls(request: pytest.FixtureRequest):  # type: ignore[no-untyped-def]
    return request.param


def test_success_one_call(engine_cls) -> None:  # type: ignore[no-untyped-def]
    c = ScriptedClient([GOOD])
    v = engine_cls(c).triage(F, B)
    assert v.label is VerdictLabel.LIKELY_TRUE and len(c.calls) == 1
    assert (v.tokens_in, v.tokens_out, v.cached, v.error) == (100, 20, False, None)
    assert v.model_id == "test-model" and v.evidence[0].line == 42


def test_cache_hit_skips_model(engine_cls) -> None:  # type: ignore[no-untyped-def]
    c = ScriptedClient([GOOD])
    e = engine_cls(c, VerdictCache())
    e.triage(F, B)
    v2 = e.triage(F, B)
    assert len(c.calls) == 1 and v2.cached and v2.tokens_in == 0


def test_bad_json_then_good_uses_two_calls_with_repair(engine_cls) -> None:  # type: ignore[no-untyped-def]
    c = ScriptedClient(["không phải json", GOOD])
    v = engine_cls(c).triage(F, B)
    assert v.label is VerdictLabel.LIKELY_TRUE and len(c.calls) == 2
    assert c.calls[1][-1]["role"] == "user" and "rejected" in c.calls[1][-1]["content"]
    assert (v.tokens_in, v.tokens_out) == (200, 40)


def test_bad_json_twice_is_invalid_and_never_more_than_two_calls(engine_cls) -> None:  # type: ignore[no-untyped-def]
    c = ScriptedClient(["x", "y", GOOD])
    v = engine_cls(c).triage(F, B)
    assert v.label is VerdictLabel.INVALID and len(c.calls) == 2 and v.error


def test_truncated_output_is_rejected(engine_cls) -> None:  # type: ignore[no-untyped-def]
    c = ScriptedClient([GOOD, GOOD], finish="length")
    v = engine_cls(c).triage(F, B)
    assert v.label is VerdictLabel.INVALID and len(c.calls) == 2


def test_budget_exhausted_returns_unknown_without_call(engine_cls) -> None:  # type: ignore[no-untyped-def]
    c = ScriptedClient([GOOD])
    budget = BudgetGuard(per_pr_tokens=10)
    budget.record(10)
    v = engine_cls(c, budget=budget).triage(F, B)
    assert v.label is VerdictLabel.UNKNOWN and v.error == "budget" and not c.calls


def test_llm_error_returns_unknown_and_is_not_cached(engine_cls) -> None:  # type: ignore[no-untyped-def]
    c = ScriptedClient([LlmError("mạng"), GOOD])
    cache = VerdictCache()
    e = engine_cls(c, cache)
    v = e.triage(F, B)
    assert v.label is VerdictLabel.UNKNOWN and (v.error or "").startswith("llm_error")
    assert e.triage(F, B).label is VerdictLabel.LIKELY_TRUE


def test_redacts_secrets_before_sending(engine_cls) -> None:  # type: ignore[no-untyped-def]
    from dataclasses import replace

    from pr_triage.core.models import ContextSlice

    secret_slice = ContextSlice(F.file, 40, 44, "sink", 'String password = "hunter2hunter2";')
    b = replace(B, slices=(secret_slice,))
    c = ScriptedClient([GOOD])
    engine_cls(c).triage(F, b)
    assert "hunter2hunter2" not in json.dumps(c.calls)


def test_engines_agree_on_same_input() -> None:
    plain = PlainTriageEngine(ScriptedClient(["x", GOOD])).triage(F, B)
    graph = TriageEngine(ScriptedClient(["x", GOOD])).triage(F, B)
    assert plain == graph


def test_both_satisfy_llm_port() -> None:
    a: LlmPort = PlainTriageEngine(ScriptedClient([]))
    b: LlmPort = TriageEngine(ScriptedClient([]))
    assert a is not None and b is not None
