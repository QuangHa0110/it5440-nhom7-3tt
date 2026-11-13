"""Thử trên cổng LLM thật. Chạy khi có PR_TRIAGE_LLM_API_KEY, bỏ qua nếu không."""

import os
from dataclasses import replace

import pytest

from pr_triage.context import SnippetProvider
from pr_triage.core.models import Finding, VerdictLabel
from pr_triage.llm.client import OpenAICompatClient
from pr_triage.llm.config import LlmConfig
from pr_triage.llm.engine import PlainTriageEngine, TriageEngine
from tests.factories import make_finding
from tests.helpers import FIXTURE

pytestmark = pytest.mark.integration

if not os.environ.get("PR_TRIAGE_LLM_API_KEY") or not os.environ.get("PR_TRIAGE_LLM_MODEL"):
    pytest.skip("không có PR_TRIAGE_LLM_API_KEY hoặc PR_TRIAGE_LLM_MODEL", allow_module_level=True)


def _finding() -> Finding:
    return replace(make_finding(path="src/app/OrderDao.java", line=10, symbol="OrderDao.find"))


@pytest.mark.parametrize("engine_cls", [PlainTriageEngine, TriageEngine])
def test_live_verdict_is_valid(engine_cls: type) -> None:
    cfg = replace(LlmConfig.from_env(), allow_external=True)
    f = _finding()
    b = SnippetProvider(radius=12).extract(f, FIXTURE)
    v = engine_cls(OpenAICompatClient(cfg)).triage(f, b)
    assert v.error is None and v.label is not VerdictLabel.INVALID
    assert v.tokens_in > 0 and v.model_id == cfg.model
