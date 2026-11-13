"""Che secret trước khi gửi mã cho LLM (proposal 6.6)."""

from __future__ import annotations

import re

_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(
        r"(?i)((?:api[_-]?key|secret|token|passwd|password|pwd)[\w]*\s*[:=]\s*[\"']?)([^\s\"';,)]{6,})"
    ),
)
MASK = "[REDACTED]"


def redact(text: str) -> tuple[str, int]:
    """Trả về (văn bản đã che, số chỗ đã che)."""
    total = 0

    def sub_all(pattern: re.Pattern[str], s: str) -> str:
        nonlocal total
        if pattern.groups:
            s, n = pattern.subn(lambda m: m.group(1) + MASK, s)
        else:
            s, n = pattern.subn(MASK, s)
        total += n
        return s

    for p in _PATTERNS:
        text = sub_all(p, text)
    return text, total
