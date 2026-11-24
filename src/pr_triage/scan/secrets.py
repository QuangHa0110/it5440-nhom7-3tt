"""Bộ quét secret (ADR 0013). Giá trị secret bị che ngay khi phát hiện, không lưu bản nguyên."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from pr_triage.core.models import RawFinding
from pr_triage.core.secrets import find_kinds, mask

_SKIP_DIRS = {".git", "node_modules", "target", "build", "dist", "vendor", ".gradle", ".venv"}
_MAX_BYTES = 1_000_000


class SecretScanner:
    name = "secrets"

    def __init__(self, max_bytes: int = _MAX_BYTES) -> None:
        self._max = max_bytes

    def scan(self, checkout: Path, paths: Sequence[str] | None = None) -> list[RawFinding]:
        out: list[RawFinding] = []
        files = [checkout / p for p in paths] if paths else sorted(checkout.rglob("*"))
        for path in files:
            rel = path.relative_to(checkout)
            if (
                not path.is_file()
                or _SKIP_DIRS.intersection(rel.parts)
                or path.stat().st_size > self._max
            ):
                continue
            data = path.read_bytes()
            if b"\x00" in data[:4096]:
                continue
            for lineno, line in enumerate(data.decode("utf-8", "replace").splitlines(), 1):
                for kind in dict.fromkeys(find_kinds(line)):
                    masked, _ = mask(line)
                    out.append(
                        RawFinding(
                            tool=self.name,
                            rule_id=f"secret.{kind}",
                            message=f"Có thể là secret ({kind}), giá trị đã được che",
                            severity="high",
                            file=rel.as_posix(),
                            line_start=lineno,
                            line_end=lineno,
                            cwe="CWE-798",
                            snippet=masked.strip(),
                        )
                    )
        return out
