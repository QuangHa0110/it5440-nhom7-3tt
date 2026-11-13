"""Danh mục nguồn, sink và hàm làm sạch, nạp từ configs/context/*.yml."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SinkSpec:
    kind: str
    methods: frozenset[str] = frozenset()
    constructors: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Catalog:
    sources: tuple[tuple[re.Pattern[str], str], ...]
    parameter_annotations: dict[str, str]
    sinks: dict[str, SinkSpec]
    sanitizer_name: re.Pattern[str]
    entry_points: frozenset[str] = frozenset()
    framework_types: frozenset[str] = frozenset()
    version: int = 1
    raw: dict[str, Any] = field(default_factory=dict, compare=False, repr=False)

    def source_kind(self, expr_text: str) -> str | None:
        for pattern, kind in self.sources:
            if pattern.search(expr_text):
                return kind
        return None

    def looks_like_sanitizer(self, name: str) -> bool:
        return bool(self.sanitizer_name.search(name))

    def sink_for(self, cwe: str | None) -> SinkSpec | None:
        return self.sinks.get(cwe or "")

    def any_sink_method(self) -> frozenset[str]:
        return frozenset(m for s in self.sinks.values() for m in s.methods)


def load_catalog(path: Path) -> Catalog:
    data = yaml.safe_load(path.read_text("utf-8"))
    sinks = {
        cwe: SinkSpec(
            kind=spec["kind"],
            methods=frozenset(spec.get("methods", [])),
            constructors=frozenset(spec.get("constructors", [])),
        )
        for cwe, spec in data.get("sinks", {}).items()
    }
    return Catalog(
        sources=tuple((re.compile(s["regex"]), s["kind"]) for s in data.get("sources", [])),
        parameter_annotations={a["name"]: a["kind"] for a in data.get("parameter_annotations", [])},
        sinks=sinks,
        sanitizer_name=re.compile(data.get("sanitizer_name_regex", r"(?!)")),
        entry_points=frozenset(data.get("entry_points", [])),
        framework_types=frozenset(data.get("framework_types", [])),
        version=int(data.get("version", 1)),
        raw=data,
    )
