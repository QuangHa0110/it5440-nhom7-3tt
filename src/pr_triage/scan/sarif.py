"""Đọc SARIF 2.1.0 thành `RawFinding`, giữ vết luồng dữ liệu nếu công cụ có."""

from __future__ import annotations

import json
import re
from typing import Any

from pr_triage.core.models import FlowStep, RawFinding

_LEVEL = {"error": "high", "warning": "medium", "note": "low", "none": "low"}
_CWE = re.compile(r"CWE-\d+", re.IGNORECASE)


def _rule_index(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rules = run.get("tool", {}).get("driver", {}).get("rules", []) or []
    return {r["id"]: r for r in rules if "id" in r}


def _cwe(rule: dict[str, Any]) -> str | None:
    tags = rule.get("properties", {}).get("tags", []) or []
    for tag in tags:
        m = _CWE.search(str(tag))
        if m:
            return m.group(0).upper()
    return None


def _flow(result: dict[str, Any]) -> tuple[FlowStep, ...]:
    steps: list[FlowStep] = []
    for cf in result.get("codeFlows", []) or []:
        for tf in cf.get("threadFlows", []) or []:
            for loc in tf.get("locations", []) or []:
                inner = loc.get("location", {})
                phys = inner.get("physicalLocation", {})
                uri = phys.get("artifactLocation", {}).get("uri")
                line = phys.get("region", {}).get("startLine")
                if uri and line:
                    steps.append(FlowStep(uri, int(line), inner.get("message", {}).get("text", "")))
        if steps:
            break
    return tuple(steps)


def parse_sarif(text: str, tool: str, local_rule_ids: tuple[str, ...] = ()) -> list[RawFinding]:
    """`local_rule_ids` dùng để bỏ tiền tố đường dẫn mà Semgrep thêm vào id luật cục bộ."""
    data = json.loads(text)
    out: list[RawFinding] = []
    for run in data.get("runs", []):
        rules = _rule_index(run)
        for res in run.get("results", []) or []:
            raw_id = res.get("ruleId", "")
            rule = rules.get(raw_id, {})
            locs = res.get("locations") or []
            if not locs:
                continue
            phys = locs[0].get("physicalLocation", {})
            region = phys.get("region", {})
            uri = phys.get("artifactLocation", {}).get("uri", "")
            start = int(region.get("startLine", 1))
            level = res.get("level") or rule.get("defaultConfiguration", {}).get("level", "warning")
            out.append(
                RawFinding(
                    tool=tool,
                    rule_id=_strip_prefix(raw_id, local_rule_ids),
                    message=res.get("message", {}).get("text", ""),
                    severity=_LEVEL.get(level, "medium"),
                    file=uri,
                    line_start=start,
                    line_end=int(region.get("endLine", start)),
                    cwe=_cwe(rule),
                    snippet=region.get("snippet", {}).get("text", ""),
                    flow=_flow(res),
                )
            )
    return out


def _strip_prefix(rule_id: str, local_ids: tuple[str, ...]) -> str:
    for local in local_ids:
        if rule_id == local or rule_id.endswith("." + local):
            return local
    return rule_id
