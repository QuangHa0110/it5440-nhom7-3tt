"""Che secret trước khi gửi mã cho LLM (proposal 6.6). Mẫu nhận diện ở core/secrets.py."""

from __future__ import annotations

from pr_triage.core.secrets import MASK, mask

__all__ = ["MASK", "redact"]


def redact(text: str) -> tuple[str, int]:
    """Trả về (văn bản đã che, số chỗ đã che)."""
    return mask(text)
