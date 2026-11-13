"""Cấu hình LLM từ biến môi trường (ADR 0008). Khóa không bao giờ vào repo hay log."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from urllib.parse import urlparse

LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    model: str
    api_key: str = field(default="", repr=False)
    allow_external: bool = False
    allowed_hosts: frozenset[str] = LOCAL_HOSTS
    timeout_s: float = 120.0
    max_tokens: int = 1500
    temperature: float = 0.0
    seed: int = 0
    json_mode: bool = False

    @property
    def host(self) -> str:
        return urlparse(self.base_url).hostname or ""

    def host_allowed(self) -> bool:
        return self.allow_external or self.host in self.allowed_hosts

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> LlmConfig:
        e = os.environ if env is None else env
        return cls(
            base_url=e.get("PR_TRIAGE_LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/"),
            model=e.get("PR_TRIAGE_LLM_MODEL", ""),
            api_key=e.get("PR_TRIAGE_LLM_API_KEY", ""),
            allow_external=e.get("PR_TRIAGE_LLM_ALLOW_EXTERNAL", "0") in ("1", "true", "yes"),
            json_mode=e.get("PR_TRIAGE_LLM_JSON_MODE", "0") in ("1", "true", "yes"),
        )
