"""Phân tích và kiểm tra đầu ra của LLM (ADR 0003 D4)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from pr_triage.core.models import ContextBundle, EvidenceItem, VerdictLabel

LABELS = ("likely_true", "likely_false", "unknown")
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


@dataclass(frozen=True)
class ParsedVerdict:
    label: VerdictLabel
    explanation: str
    evidence: tuple[EvidenceItem, ...]
    missing_context: tuple[str, ...]


class VerdictFormatError(ValueError):
    pass


def _first_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise VerdictFormatError("không có đối tượng JSON")
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise VerdictFormatError("JSON bị cắt cụt")


def extract_json(text: str) -> object:
    text = _THINK.sub("", text).strip()
    m = _FENCE.search(text)
    chunk = m.group(1) if m else _first_object(text)
    try:
        return json.loads(chunk)
    except json.JSONDecodeError as exc:
        raise VerdictFormatError(f"JSON sai cú pháp: {exc.msg}") from exc


def _norm(path: str) -> str:
    return path.replace("\\", "/").removeprefix("./")


def validate_verdict(text: str, bundle: ContextBundle, finding_id: str) -> ParsedVerdict:
    data = extract_json(text)
    if not isinstance(data, dict):
        raise VerdictFormatError("gốc không phải đối tượng")
    for key in ("label", "explanation", "evidence", "missing_context"):
        if key not in data:
            raise VerdictFormatError(f"thiếu trường {key}")
    label = data["label"]
    if label not in LABELS:
        raise VerdictFormatError(f"label không hợp lệ: {label!r}")
    if "finding_id" in data and data["finding_id"] != finding_id:
        raise VerdictFormatError("finding_id không khớp")
    if not isinstance(data["explanation"], str):
        raise VerdictFormatError("explanation phải là chuỗi")
    if not isinstance(data["evidence"], list) or not isinstance(data["missing_context"], list):
        raise VerdictFormatError("evidence và missing_context phải là mảng")
    evidence: list[EvidenceItem] = []
    for item in data["evidence"]:
        if not isinstance(item, dict) or not isinstance(item.get("file"), str):
            raise VerdictFormatError("mục evidence sai dạng")
        line = item.get("line")
        if isinstance(line, bool) or not isinstance(line, int):
            raise VerdictFormatError("evidence.line phải là số nguyên")
        if not any(
            _norm(s.file) == _norm(item["file"]) and s.start <= line <= s.end for s in bundle.slices
        ):
            raise VerdictFormatError(
                f"bằng chứng {item['file']}:{line} nằm ngoài ngữ cảnh đã cung cấp"
            )
        evidence.append(EvidenceItem(item["file"], line, str(item.get("note", ""))))
    if label in ("likely_true", "likely_false") and not evidence:
        raise VerdictFormatError("nhãn chắc chắn phải kèm ít nhất một bằng chứng")
    return ParsedVerdict(
        VerdictLabel(label),
        data["explanation"],
        tuple(evidence),
        tuple(str(x) for x in data["missing_context"]),
    )
