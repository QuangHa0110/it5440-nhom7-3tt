"""Cache nhận định (ADR 0003, kiến trúc mục 8.2). Khóa gồm mọi thứ ảnh hưởng đến đầu ra."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pr_triage.core.models import Verdict
from pr_triage.core.serde import from_json, to_json


def cache_key(
    fingerprint: str,
    bundle_hash: str,
    prompt_version: str,
    model_id: str,
    params: dict[str, object],
) -> str:
    raw = json.dumps([fingerprint, bundle_hash, prompt_version, model_id, params], sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


class VerdictCache:
    def __init__(self, directory: Path | None = None) -> None:
        self._mem: dict[str, Verdict] = {}
        self._dir = directory
        if directory:
            directory.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> Verdict | None:
        if key in self._mem:
            return self._mem[key]
        if self._dir and (p := self._dir / f"{key}.json").exists():
            v = from_json(Verdict, p.read_text("utf-8"))
            self._mem[key] = v
            return v
        return None

    def put(self, key: str, verdict: Verdict) -> None:
        self._mem[key] = verdict
        if self._dir:
            (self._dir / f"{key}.json").write_text(to_json(verdict), "utf-8")
