"""Pipeline từ chối chạy khi bộ luật tải về thiếu hoặc lệch mã băm (ADR 0015 D3)."""

from pathlib import Path

import pytest

from pr_triage import cli
from pr_triage.core.errors import ScanError
from pr_triage.pipeline.build import BuildOptions, build_pipeline
from pr_triage.scan.rulesets import Ruleset, dump_lock, sha256_bytes
from tests.fakes import FakeLlm
from tests.helpers import REPO_ROOT

RULES = "rules:\n- id: x\n  languages: [java]\n  message: m\n  severity: INFO\n  pattern: foo()\n"


def _setup(tmp: Path) -> tuple[Path, Path]:
    rules = tmp / "semgrep-default.yml"
    rules.write_text(RULES, "utf-8")
    lock = tmp / "rulesets.lock"
    dump_lock(lock, [Ruleset("default", "u", "data/rules/semgrep-default.yml", "2026-11-19",
                             sha256_bytes(rules.read_bytes()), 1)])  # fmt: skip
    return rules, lock


def _opts(tmp: Path, rules: Path, lock: Path) -> BuildOptions:
    return BuildOptions(
        rules=[str(rules)], rules_lock=str(lock), db=str(tmp / "s.sqlite"),
        catalog=str(REPO_ROOT / "configs/context/java.yml"),
    )  # fmt: skip


def test_locked_rules_build(tmp_path: Path) -> None:
    rules, lock = _setup(tmp_path)
    _, store = build_pipeline(_opts(tmp_path, rules, lock), llm=FakeLlm())
    store.close()


def test_tampered_rules_refuse_to_build(tmp_path: Path) -> None:
    rules, lock = _setup(tmp_path)
    rules.write_text(RULES.replace("foo", "bar"), "utf-8")
    with pytest.raises(ScanError, match="lệch mã băm"):
        build_pipeline(_opts(tmp_path, rules, lock), llm=FakeLlm())
    assert not (tmp_path / "s.sqlite").exists()


def test_registry_file_without_lock_is_rejected(tmp_path: Path) -> None:
    rules, _ = _setup(tmp_path)
    with pytest.raises(ScanError, match="lock"):
        build_pipeline(_opts(tmp_path, rules, tmp_path / "missing.lock"), llm=FakeLlm())


def test_cli_reports_missing_rules_without_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _, lock = _setup(tmp_path)
    code = cli.main([
        "run", "--repo", str(tmp_path), "--base", "a", "--head", "b", "--pr", "1",
        "--rules", str(tmp_path / "nowhere" / "semgrep-default.yml"),
        "--rules-lock", str(lock), "--db", str(tmp_path / "s.sqlite"),
    ])  # fmt: skip
    assert code == 2
    assert "fetch_semgrep_rules" in capsys.readouterr().err
