"""Script tải bộ luật: ghi file vào data/, ghi lock đúng mã băm, --frozen và --verify bắt lệch."""

import sys
from pathlib import Path

import httpx
import pytest

from pr_triage.core.errors import ScanError
from pr_triage.scan.rulesets import load_lock, sha256_bytes
from tests.helpers import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import fetch_semgrep_rules as fsr  # noqa: E402

RULES = """rules:
- id: a.java-rule
  languages: [java]
  message: m
  severity: WARNING
  pattern: foo()
- id: b.python-rule
  languages: [python]
  message: m
  severity: WARNING
  pattern: bar()
"""


def transport(body: str, status: int = 200) -> httpx.MockTransport:
    def handler(req: httpx.Request) -> httpx.Response:
        assert req.url.path == "/c/p/default"
        return httpx.Response(status, text=body)

    return httpx.MockTransport(handler)


@pytest.fixture(autouse=True)
def no_semgrep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fsr, "semgrep_version", lambda: "1.0.0")


def test_fetch_writes_file_and_lock(tmp_path: Path) -> None:
    lock = tmp_path / "configs" / "rulesets.lock"
    lock.parent.mkdir()
    r = fsr.fetch("default", tmp_path, lock, [], transport=transport(RULES), today="2026-11-19")
    data = (tmp_path / "data/rules/semgrep-default.yml").read_bytes()
    assert r.sha256 == sha256_bytes(data) and r.rules == 2
    assert load_lock(lock)["default"].sha256 == r.sha256
    assert "a.java-rule" not in lock.read_text("utf-8")  # lock không chứa luật
    assert fsr.verify(tmp_path, lock) == []


def test_verify_detects_one_byte_change(tmp_path: Path) -> None:
    lock = tmp_path / "rulesets.lock"
    fsr.fetch("default", tmp_path, lock, [], transport=transport(RULES))
    f = tmp_path / "data/rules/semgrep-default.yml"
    f.write_bytes(f.read_bytes()[:-1] + b"X")
    assert (
        fsr.verify(tmp_path, lock)
        and fsr.main(["--verify", "--root", str(tmp_path), "--lock", str(lock)]) == 1
    )


def test_frozen_rejects_changed_registry(tmp_path: Path) -> None:
    lock = tmp_path / "rulesets.lock"
    fsr.fetch("default", tmp_path, lock, [], transport=transport(RULES))
    with pytest.raises(ScanError, match="registry đã đổi"):
        fsr.fetch("default", tmp_path, lock, [], frozen=True, transport=transport(RULES + "# x\n"))
    fsr.fetch("default", tmp_path, lock, [], frozen=True, transport=transport(RULES))


def test_frozen_reuses_locked_languages(tmp_path: Path) -> None:
    lock = tmp_path / "rulesets.lock"
    first = fsr.fetch("default", tmp_path, lock, ["java"], transport=transport(RULES))
    assert first.rules == 1 and first.languages == ("java",)
    again = fsr.fetch("default", tmp_path, lock, [], frozen=True, transport=transport(RULES))
    assert again.sha256 == first.sha256


def test_http_error_and_non_yaml_are_errors(tmp_path: Path) -> None:
    lock = tmp_path / "rulesets.lock"
    with pytest.raises(ScanError, match="HTTP 401"):
        fsr.fetch("default", tmp_path, lock, [], transport=transport("", 401))
    with pytest.raises(ScanError):
        fsr.fetch("default", tmp_path, lock, [], transport=transport("<html>login</html>"))
    assert not lock.exists()
