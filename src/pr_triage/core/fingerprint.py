"""Dấu vân tay cảnh báo (ADR 0011). Không dùng số dòng."""

from __future__ import annotations

import hashlib
import re

FP_VERSION = 1

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT = re.compile(r"//[^\n]*")
_WS = re.compile(r"\s+")
_PUNCT_WS = re.compile(r"\s*([^\w\s])\s*")


def normalize_snippet(text: str) -> str:
    """Bỏ chú thích kiểu C, gộp khoảng trắng và bỏ khoảng trắng quanh dấu câu."""
    text = _BLOCK_COMMENT.sub(" ", text)
    text = _LINE_COMMENT.sub(" ", text)
    return _PUNCT_WS.sub(r"\1", _WS.sub(" ", text).strip())


def normalize_rule(rule_id: str) -> str:
    return rule_id.strip().lower()


def fingerprint(
    rule_id: str,
    path: str,
    symbol: str | None,
    snippet: str,
    ordinal: int,
    version: int = FP_VERSION,
) -> str:
    parts = [
        f"v{version}",
        normalize_rule(rule_id),
        path.replace("\\", "/").lstrip("./"),
        symbol or "",
        normalize_snippet(snippet),
        str(ordinal),
    ]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def finding_id(fp: str) -> str:
    return fp[:12]
