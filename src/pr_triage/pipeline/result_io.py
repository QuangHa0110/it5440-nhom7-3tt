"""triage-result.json: trao đổi giữa job triage và job publish, kiểm tra ở cả hai đầu (ADR 0007)."""

from __future__ import annotations

import json
from pathlib import Path

from pr_triage.core.models import TriageResult
from pr_triage.core.serde import from_plain, to_plain

SCHEMA_VERSION = 1


class ResultFormatError(ValueError):
    pass


def dumps(result: TriageResult) -> str:
    return json.dumps(
        {"schema_version": SCHEMA_VERSION, "result": to_plain(result)}, ensure_ascii=False, indent=2
    )


def loads(text: str) -> TriageResult:
    try:
        data = json.loads(text)
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ResultFormatError(f"schema_version không hỗ trợ: {data.get('schema_version')!r}")
        return from_plain(TriageResult, data["result"])
    except ResultFormatError:
        raise
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ResultFormatError(f"triage-result.json sai định dạng: {exc}") from exc


def write(result: TriageResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(result), "utf-8")


def read(path: Path) -> TriageResult:
    return loads(path.read_text("utf-8"))
