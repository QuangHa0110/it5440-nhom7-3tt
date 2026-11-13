"""Phân tích CODEOWNERS: quy tắc khớp cuối cùng thắng. Không hỗ trợ phủ định và nhóm mục."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from pr_triage.pipeline.pathglob import matches


@dataclass(frozen=True)
class Rule:
    pattern: str
    owners: tuple[str, ...]


def parse(text: str) -> list[Rule]:
    rules: list[Rule] = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("["):
            continue
        parts = line.split()
        if parts[0].startswith("!") or len(parts) < 2:
            continue
        owners = tuple(o for o in parts[1:] if o.startswith("@"))
        if owners:
            rules.append(Rule(parts[0], owners))
    return rules


def owners_for(files: Iterable[str], rules: list[Rule]) -> list[str]:
    out: list[str] = []
    for f in files:
        hit = next((r for r in reversed(rules) if matches(r.pattern, f)), None)
        for o in hit.owners if hit else ():
            if o not in out:
                out.append(o)
    return out
