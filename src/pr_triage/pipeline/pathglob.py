"""So khớp đường dẫn kiểu gitignore, dùng cho paths.include/exclude và CODEOWNERS."""

from __future__ import annotations

import re
from functools import lru_cache


@lru_cache(maxsize=512)
def compile_glob(pattern: str) -> re.Pattern[str]:
    """Quy tắc: `**` khớp mọi cấp, `*` không qua dấu `/`, mẫu không có `/` khớp tên tệp ở mọi cấp,
    mẫu bắt đầu bằng `/` neo ở gốc, mẫu kết thúc bằng `/` khớp mọi thứ dưới thư mục."""
    pat = pattern.strip()
    anchored = pat.startswith("/")
    pat = pat.lstrip("/")
    pat = pat.rstrip("/")
    has_slash = "/" in pat
    out = ""
    i = 0
    while i < len(pat):
        c = pat[i]
        if pat.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pat.startswith("**", i):
            out += ".*"
            i += 2
        elif c == "*":
            out += "[^/]*"
            i += 1
        elif c == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(c)
            i += 1
    prefix = "" if (anchored or has_slash) else "(?:.*/)?"
    suffix = "(?:/.*)?"  # mẫu khớp thư mục thì khớp cả mọi thứ bên dưới
    return re.compile(f"^{prefix}{out}{suffix}$")


def matches(pattern: str, path: str) -> bool:
    return bool(compile_glob(pattern).match(path.replace("\\", "/").lstrip("./")))


def any_match(patterns: tuple[str, ...] | list[str], path: str) -> bool:
    return any(matches(p, path) for p in patterns)
