"""Mẫu nhận diện secret, dùng chung cho bộ quét và bộ che trước khi gửi LLM (ADR 0013)."""

from __future__ import annotations

import re
from dataclasses import dataclass

MASK = "[REDACTED]"


@dataclass(frozen=True)
class SecretPattern:
    kind: str
    regex: re.Pattern[str]
    value_group: int = 0  # nhóm chứa giá trị cần che; 0 là toàn bộ chuỗi khớp


PATTERNS: tuple[SecretPattern, ...] = (
    SecretPattern(
        "private-key",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----(?:.*?-----END [A-Z ]*PRIVATE KEY-----)?", re.DOTALL
        ),
    ),
    SecretPattern("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    SecretPattern("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    SecretPattern("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    SecretPattern("api-key", re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")),
    SecretPattern(
        "jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
    ),
    SecretPattern(
        "credential-assignment",
        re.compile(
            r"(?i)((?:api[_-]?key|secret|token|passwd|password|pwd)[\w]*\s*[:=]\s*[\"']?)([^\s\"';,)]{6,})"
        ),
        value_group=2,
    ),
)

_TEMPLATE = re.compile(r"^(\$\{|\$\(|\{\{|<|%\()|^(os\.|System\.|process\.env|getenv)")


def is_reference(value: str) -> bool:
    """Giá trị chỉ là tham chiếu biến môi trường hoặc mẫu, không phải secret."""
    return bool(_TEMPLATE.search(value))


def mask(text: str) -> tuple[str, int]:
    """Trả về (văn bản đã che, số chỗ đã che)."""
    total = 0
    for p in PATTERNS:
        if p.value_group:

            def repl(m: re.Match[str], g: int = p.value_group) -> str:
                nonlocal total
                if is_reference(m.group(g)):
                    return m.group(0)
                total += 1
                return m.group(1) + MASK

            text = p.regex.sub(repl, text)
        else:
            text, n = p.regex.subn(MASK, text)
            total += n
    return text, total


def find_kinds(text: str) -> list[str]:
    """Các loại secret có trong `text` (bỏ qua tham chiếu biến môi trường)."""
    kinds: list[str] = []
    for p in PATTERNS:
        for m in p.regex.finditer(text):
            if p.value_group and is_reference(m.group(p.value_group)):
                continue
            kinds.append(p.kind)
    return kinds
