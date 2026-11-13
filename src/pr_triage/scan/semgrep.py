"""Bộ chuyển đổi Semgrep CE: chạy như tiến trình con và đọc SARIF (ADR 0005)."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from pr_triage.core.errors import ScanError
from pr_triage.core.models import RawFinding
from pr_triage.scan.sarif import parse_sarif

_RULE_ID = re.compile(r"^\s*-\s*id:\s*(\S+)", re.MULTILINE)


def _find_semgrep() -> str:
    venv_bin = Path(sys.executable).parent / "semgrep"
    if venv_bin.exists():
        return str(venv_bin)
    found = shutil.which("semgrep")
    if not found:
        raise ScanError("không tìm thấy semgrep")
    return found


def _local_rule_ids(configs: Sequence[str]) -> tuple[str, ...]:
    ids: list[str] = []
    for c in configs:
        p = Path(c)
        if p.is_file():
            ids.extend(_RULE_ID.findall(p.read_text("utf-8")))
    return tuple(ids)


class SemgrepAdapter:
    name = "semgrep"

    def __init__(
        self, configs: Sequence[str], timeout_s: int = 300, executable: str | None = None
    ) -> None:
        self._configs = [str(Path(c).resolve()) if Path(c).exists() else c for c in configs]
        self._timeout = timeout_s
        self._exe = executable

    def scan(self, checkout: Path, paths: Sequence[str] | None = None) -> list[RawFinding]:
        exe = self._exe or _find_semgrep()
        with tempfile.TemporaryDirectory(prefix="pr-triage-semgrep-") as tmp:
            out = Path(tmp) / "out.sarif"
            cmd = [
                exe,
                "scan",
                "--sarif-output",
                str(out),
                "--metrics=off",
                "--quiet",
                "--disable-version-check",
                "--timeout",
                "30",
            ]
            for c in self._configs:
                cmd += ["--config", c]
            cmd += list(paths) if paths else ["."]
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=checkout,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise ScanError(f"semgrep quá {self._timeout}s") from exc
            if proc.returncode not in (0, 1) or not out.exists():
                raise ScanError(f"semgrep lỗi ({proc.returncode}): {proc.stderr[-400:]}")
            findings = parse_sarif(
                out.read_text("utf-8"), self.name, _local_rule_ids(self._configs)
            )
        return [_with_snippet(f, checkout) for f in findings]


def _with_snippet(f: RawFinding, checkout: Path) -> RawFinding:
    if f.snippet:
        return f
    path = checkout / f.file
    try:
        lines = path.read_text("utf-8", errors="replace").splitlines()
    except OSError:
        return f
    text = "\n".join(lines[max(f.line_start - 1, 0) : f.line_end])
    return RawFinding(**{**f.__dict__, "snippet": text})
