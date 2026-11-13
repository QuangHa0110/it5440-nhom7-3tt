"""Client kiểu OpenAI bằng httpx (ADR 0008). Dùng được cho cổng ngoài, Ollama và vLLM."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from pr_triage.core.errors import LlmError
from pr_triage.llm.config import LlmConfig

log = logging.getLogger("pr_triage.llm")
_RETRY_STATUS = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class ChatResult:
    text: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    finish_reason: str
    model: str


class OpenAICompatClient:
    def __init__(
        self,
        config: LlmConfig,
        transport: httpx.BaseTransport | None = None,
        max_attempts: int = 3,
        backoff_s: float = 1.0,
    ) -> None:
        self._cfg = config
        self._http = httpx.Client(timeout=config.timeout_s, transport=transport)
        self._max_attempts = max_attempts
        self._backoff = backoff_s

    @property
    def config(self) -> LlmConfig:
        return self._cfg

    def _redact(self, text: str) -> str:
        key = self._cfg.api_key
        return text.replace(key, "***") if key else text

    def chat(self, messages: list[dict[str, str]]) -> ChatResult:
        cfg = self._cfg
        if not cfg.host_allowed():
            raise LlmError(
                f"máy chủ {cfg.host!r} không nằm trong danh sách cho phép (allow_external tắt)"
            )
        body: dict[str, Any] = {
            "model": cfg.model,
            "messages": messages,
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            "seed": cfg.seed,
        }
        if cfg.json_mode:
            body["response_format"] = {"type": "json_object"}
        headers = {"Content-Type": "application/json"}
        if cfg.api_key:
            headers["Authorization"] = f"Bearer {cfg.api_key}"
        last = ""
        for attempt in range(1, self._max_attempts + 1):
            start = time.monotonic()
            try:
                resp = self._http.post(
                    f"{cfg.base_url}/chat/completions", json=body, headers=headers
                )
            except httpx.HTTPError as exc:
                last = self._redact(f"{type(exc).__name__}: {exc}")
            else:
                if resp.status_code == 200:
                    return self._parse(resp, int((time.monotonic() - start) * 1000))
                last = self._redact(f"HTTP {resp.status_code}: {resp.text[:200]}")
                if resp.status_code not in _RETRY_STATUS:
                    break
            log.warning("llm lần %d/%d lỗi: %s", attempt, self._max_attempts, last)
            if attempt < self._max_attempts:
                time.sleep(self._backoff * attempt)
        raise LlmError(last)

    def _parse(self, resp: httpx.Response, latency_ms: int) -> ChatResult:
        try:
            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return ChatResult(
                text=choice["message"]["content"] or "",
                tokens_in=int(usage.get("prompt_tokens", 0)),
                tokens_out=int(usage.get("completion_tokens", 0)),
                latency_ms=latency_ms,
                finish_reason=str(choice.get("finish_reason", "")),
                model=str(data.get("model", self._cfg.model)),
            )
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise LlmError(f"phản hồi sai định dạng: {self._redact(str(exc))}") from exc

    def close(self) -> None:
        self._http.close()
