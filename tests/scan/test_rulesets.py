"""Khóa bộ luật bằng mã băm (ADR 0019): lock, lọc ngôn ngữ, kiểm tra khi chạy."""

from pathlib import Path

import pytest

from pr_triage.core.errors import ScanError
from pr_triage.scan.rulesets import (
    Ruleset,
    count_rules,
    dump_lock,
    filter_languages,
    load_lock,
    sha256_bytes,
    verify_rules,
)

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


def _lock(tmp: Path, text: str, name: str = "default") -> tuple[Path, Path]:
    rules = tmp / "data" / "rules" / f"semgrep-{name}.yml"
    rules.parent.mkdir(parents=True)
    rules.write_text(text, "utf-8")
    lock = tmp / "rulesets.lock"
    entry = Ruleset(
        name=name, url="u", file=f"data/rules/semgrep-{name}.yml", fetched="2026-11-19",
        sha256=sha256_bytes(rules.read_bytes()), rules=2,
    )  # fmt: skip
    dump_lock(lock, [entry])
    return rules, lock


def test_lock_roundtrip(tmp_path: Path) -> None:
    _, lock = _lock(tmp_path, RULES)
    got = load_lock(lock)["default"]
    assert got.file == "data/rules/semgrep-default.yml" and got.rules == 2
    assert "KHÔNG chứa luật" in lock.read_text("utf-8")


def test_missing_lock_is_empty(tmp_path: Path) -> None:
    assert load_lock(tmp_path / "none.lock") == {}


def test_verify_ok_and_ignores_handwritten_rules(tmp_path: Path) -> None:
    rules, lock = _lock(tmp_path, RULES)
    other = tmp_path / "java-injection.yml"
    other.write_text(RULES, "utf-8")
    checked = verify_rules([str(rules), str(other)], lock)
    assert [r.name for r in checked] == ["default"]


def test_verify_rejects_tampered_file(tmp_path: Path) -> None:
    rules, lock = _lock(tmp_path, RULES)
    rules.write_text(RULES + "\n", "utf-8")
    with pytest.raises(ScanError, match="lệch mã băm"):
        verify_rules([str(rules)], lock)


def test_verify_rejects_missing_file(tmp_path: Path) -> None:
    rules, lock = _lock(tmp_path, RULES)
    rules.unlink()
    with pytest.raises(ScanError, match="fetch_semgrep_rules"):
        verify_rules([str(rules)], lock)


def test_filter_languages_keeps_matching_rules() -> None:
    out = filter_languages(RULES, ["Java"])
    assert count_rules(out) == 1 and "a.java-rule" in out and "python" not in out


def test_filter_languages_empty_result_is_error() -> None:
    with pytest.raises(ScanError):
        filter_languages(RULES, ["go"])


def test_count_rules_rejects_non_ruleset() -> None:
    with pytest.raises(ScanError):
        count_rules("<html>login</html>")
