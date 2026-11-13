import json

import httpx
import pytest

from pr_triage.core.errors import LlmError
from pr_triage.llm.client import OpenAICompatClient
from pr_triage.llm.config import LlmConfig

OK = {
    "model": "m",
    "choices": [{"message": {"content": '{"a":1}'}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 7, "completion_tokens": 3},
}


def cfg(**kw: object) -> LlmConfig:
    base = {
        "base_url": "https://model.example/v1",
        "model": "m",
        "api_key": "sk-secret-1234",
        "allow_external": True,
    }
    return LlmConfig(**{**base, **kw})  # type: ignore[arg-type]


def test_success_sends_auth_and_parses() -> None:
    seen: dict[str, object] = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen["auth"] = req.headers["authorization"]
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json=OK)

    c = OpenAICompatClient(cfg(), httpx.MockTransport(handler))
    r = c.chat([{"role": "user", "content": "x"}])
    assert (r.text, r.tokens_in, r.tokens_out, r.finish_reason) == ('{"a":1}', 7, 3, "stop")
    assert seen["auth"] == "Bearer sk-secret-1234"
    body = seen["body"]
    assert isinstance(body, dict) and body["temperature"] == 0.0 and body["seed"] == 0


def test_retries_on_429_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return (
            httpx.Response(429, text="slow down")
            if calls["n"] < 3
            else httpx.Response(200, json=OK)
        )

    c = OpenAICompatClient(cfg(), httpx.MockTransport(handler), backoff_s=0)
    assert c.chat([]).text == '{"a":1}' and calls["n"] == 3


def test_no_retry_on_400_and_key_not_in_error() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="bad key sk-secret-1234")

    c = OpenAICompatClient(cfg(), httpx.MockTransport(handler), backoff_s=0)
    with pytest.raises(LlmError) as e:
        c.chat([])
    assert "sk-secret-1234" not in str(e.value)


def test_external_host_refused_by_default() -> None:
    c = OpenAICompatClient(
        cfg(allow_external=False), httpx.MockTransport(lambda r: httpx.Response(200, json=OK))
    )
    with pytest.raises(LlmError, match="allow_external"):
        c.chat([])


def test_localhost_allowed_without_flag() -> None:
    c = OpenAICompatClient(
        cfg(base_url="http://localhost:11434/v1", allow_external=False),
        httpx.MockTransport(lambda r: httpx.Response(200, json=OK)),
    )
    assert c.chat([]).tokens_out == 3


def test_bad_payload_raises() -> None:
    c = OpenAICompatClient(cfg(), httpx.MockTransport(lambda r: httpx.Response(200, json={"x": 1})))
    with pytest.raises(LlmError):
        c.chat([])


def test_config_repr_hides_key_and_from_env() -> None:
    c = cfg()
    assert "sk-secret" not in repr(c)
    e = LlmConfig.from_env(
        {
            "PR_TRIAGE_LLM_BASE_URL": "http://h/v1/",
            "PR_TRIAGE_LLM_MODEL": "x",
            "PR_TRIAGE_LLM_ALLOW_EXTERNAL": "1",
        }
    )
    assert (e.base_url, e.model, e.allow_external) == ("http://h/v1", "x", True)
