"""Làm sạch nội dung do mô hình hoặc mã của PR sinh ra trước khi đưa vào comment (ADR 0014 D4)."""

from __future__ import annotations

import re

_ZWSP = "​"
_MENTION = re.compile(r"@(?=[A-Za-z0-9_])")
_ISSUE_REF = re.compile(r"(?<![\w&])#(?=\d)")
_URL = re.compile(r"(?i)\b(https?|ftp)://")
_LINK = re.compile(r"\]\(")
_SPACE = re.compile(r"\s+")


def clean(text: str, limit: int = 600) -> str:
    """Vô hiệu @mention, tham chiếu #n, liên kết tự động, HTML; gộp dòng; cắt độ dài."""
    t = _SPACE.sub(" ", text).strip()
    if len(t) > limit:
        t = t[: limit - 1].rstrip() + "…"
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = _MENTION.sub("@" + _ZWSP, t)
    t = _ISSUE_REF.sub("#" + _ZWSP, t)
    t = _URL.sub(lambda m: m.group(1) + _ZWSP + "://", t)
    return _LINK.sub("] (", t)


def clean_inline_code(text: str, limit: int = 200) -> str:
    """Dùng cho đường dẫn đặt trong dấu backtick."""
    t = _SPACE.sub(" ", text).strip()[:limit]
    return t.replace("`", "'")
