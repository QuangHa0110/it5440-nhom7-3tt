"""Chạy đầu cuối với Semgrep thật và LLM giả: kiểm tra mọi khâu nối đúng nhau."""

import json
import shutil
import sys
from pathlib import Path

import pytest

from pr_triage import cli
from pr_triage.core.models import RunMode, RunStatus
from pr_triage.pipeline import result_io
from pr_triage.pipeline.build import BuildOptions, build_pipeline
from tests.fakes import FakeLlm
from tests.helpers import REPO_ROOT, git, make_repo

pytestmark = pytest.mark.integration

if not (Path(sys.executable).parent / "semgrep").exists() and not shutil.which("semgrep"):
    pytest.skip("không có semgrep", allow_module_level=True)

NEW = """
    public String search(HttpServletRequest request, java.sql.Statement stmt) throws Exception {
        String name = request.getParameter("name");
        String q = "SELECT * FROM users WHERE name = '" + name + "'";
        return stmt.executeQuery(q).toString();
    }
}
"""


@pytest.fixture
def fake_llm_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pr_triage.cli.build_pipeline", lambda o: build_pipeline(o, llm=FakeLlm()))


def feature_repo(tmp_path: Path) -> Path:
    repo = make_repo(tmp_path / "r")
    git(repo, "switch", "-qc", "feature")
    c = repo / "src/app/OrderController.java"
    c.write_text(c.read_text().rstrip().rstrip("}") + NEW)
    git(repo, "commit", "-qam", "thêm tìm kiếm")
    return repo


def opts(tmp_path: Path) -> BuildOptions:
    return BuildOptions(
        rules=[str(REPO_ROOT / "configs/semgrep/java-injection.yml")],
        catalog=str(REPO_ROOT / "configs/context/java.yml"),
        db=str(tmp_path / "s.sqlite"),
        repo_alias="t",
        workers=2,
    )


def test_only_new_vulnerability_is_triaged_and_contexts_differ(tmp_path: Path) -> None:
    repo = feature_repo(tmp_path)
    pipeline, store = build_pipeline(opts(tmp_path), llm=FakeLlm())
    res = pipeline.run(repo, "main", "feature", 3)
    assert res.run.status is RunStatus.OK
    assert [f.file for f in res.findings] == ["src/app/OrderController.java"]
    assert res.findings[0].symbol == "OrderController.search"
    again = pipeline.run(repo, "main", "feature", 3)
    assert [f.finding_id for f in again.findings] == [f.finding_id for f in res.findings]
    assert again.run.run_id != res.run.run_id


def test_cli_run_writes_valid_result_and_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], fake_llm_pipeline: None
) -> None:
    repo = feature_repo(tmp_path)
    out = tmp_path / "out"
    code = cli.main(
        [
            "run",
            "--repo",
            str(repo),
            "--base",
            "main",
            "--head",
            "feature",
            "--pr",
            "9",
            "--db",
            str(tmp_path / "s.sqlite"),
            "--out",
            str(out),
            "--rules",
            str(REPO_ROOT / "configs/semgrep/java-injection.yml"),
            "--catalog",
            str(REPO_ROOT / "configs/context/java.yml"),
        ]
    )
    assert code == 0
    summary = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert summary["new_findings"] == 1 and summary["status"] == "ok"
    assert len(result_io.read(out / "triage-result.json").findings) == 1


def test_replay_over_commits(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], fake_llm_pipeline: None
) -> None:
    repo = feature_repo(tmp_path)
    code = cli.main(
        [
            "replay",
            "--repo",
            str(repo),
            "--ref",
            "feature",
            "--count",
            "3",
            "--db",
            str(tmp_path / "s.sqlite"),
            "--out",
            str(tmp_path / "o"),
            "--rules",
            str(REPO_ROOT / "configs/semgrep/java-injection.yml"),
            "--catalog",
            str(REPO_ROOT / "configs/context/java.yml"),
        ]
    )
    assert code == 0
    lines = [json.loads(x) for x in capsys.readouterr().out.strip().splitlines()]
    runs = [x for x in lines if "bỏ qua" not in x]
    assert len(runs) == 1 and runs[0]["new_findings"] == 1
    assert [x["bỏ qua"] for x in lines if "bỏ qua" in x] == ["commit gốc, không có parent"]


def test_scan_only_makes_no_llm_calls(tmp_path: Path) -> None:
    from dataclasses import replace

    from pr_triage.core.models import Variant

    repo = feature_repo(tmp_path)
    llm = FakeLlm()
    pipeline, store = build_pipeline(replace(opts(tmp_path), variants=()), llm=llm)
    res = pipeline.run(repo, "main", "feature", 3)
    assert res.run.status is RunStatus.OK and res.findings
    assert llm.calls == 0
    assert {v.variant for v in res.verdicts} == {Variant.A}
    assert len(res.verdicts) == len(res.findings)
    store.close()


def test_bc_verdicts_join_pool_after_scan_only(tmp_path: Path) -> None:
    from dataclasses import replace

    from pr_triage.evaluation import build_pool, compute_report

    repo = feature_repo(tmp_path)
    o = opts(tmp_path)
    p1, s1 = build_pipeline(replace(o, variants=()), llm=FakeLlm())
    p1.run(repo, "main", "feature", 3)
    s1.close()
    p2, s2 = build_pipeline(o, llm=FakeLlm())
    p2.run(repo, "main", "feature", 3)
    entries = build_pool(s2, "9999-01-01")
    assert entries and all(e.split == "dev" for e in entries)
    from pr_triage.core.models import Adjudication, HumanLabel

    for e in entries:
        s2.save_adjudication(Adjudication(e.finding_id, HumanLabel.TRUE, "ai-claude"))
    report = compute_report(s2, "dev", 10)
    assert {"A", "B", "C"} <= set(report["variants"])
    s2.close()


def test_scan_only_without_llm_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from dataclasses import replace

    import pr_triage.pipeline.build as build_mod

    for k in list(__import__("os").environ):
        if k.startswith("PR_TRIAGE_LLM_"):
            monkeypatch.delenv(k)

    def boom(*a: object, **k: object) -> object:
        raise AssertionError("không được tạo client LLM khi chạy chỉ quét")

    monkeypatch.setattr(build_mod, "OpenAICompatClient", boom)
    repo = feature_repo(tmp_path)
    pipeline, store = build_pipeline(replace(opts(tmp_path), variants=()))
    assert pipeline.run(repo, "main", "feature", 3).run.status is RunStatus.OK
    store.close()


def test_cli_variants_flag() -> None:
    from pr_triage.core.models import Variant

    args = cli.parser().parse_args(["replay", "--variants", "none"])
    assert cli._opts(args, RunMode.REPLAY).variants == ()
    args = cli.parser().parse_args(["replay", "--variants", "C"])
    assert cli._opts(args, RunMode.REPLAY).variants == (Variant.C,)
    args = cli.parser().parse_args(["replay"])
    assert cli._opts(args, RunMode.REPLAY).variants == (Variant.B, Variant.C)


@pytest.mark.parametrize(("side", "expected"), [("merged", {7, 8, -1}), ("first", {7})])
def test_cli_replay_records_real_pr_numbers(
    tmp_path: Path, side: str, expected: set[int], capsys: pytest.CaptureFixture[str]
) -> None:
    from pr_triage.store import SqlStore
    from tests.pipeline.test_replay_plan import history

    h = history(tmp_path)
    db = tmp_path / "s.sqlite"
    rules = str(REPO_ROOT / "configs/semgrep/java-injection.yml")
    out = str(tmp_path / "out")
    argv = ["replay", "--repo", h["repo"], "--count", "3", "--variants", "none",
            "--db", str(db), "--rules", rules, "--out", out, "--side", side]  # fmt: skip
    assert cli.main(argv) == 0
    store = SqlStore(str(db))
    assert {r.pr_number for r in store.list_runs()} == expected
    store.close()
    if side == "first":
        assert "bỏ qua" in capsys.readouterr().out


def test_budget_per_run_is_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Trần token mỗi lượt chạy chỉnh được (lượt quét mốc lịch sử có hàng chục cảnh báo)."""
    from pr_triage.core.models import RunMode
    from pr_triage.llm.config import LlmConfig
    from pr_triage.pipeline.build import BuildOptions, _engine

    monkeypatch.setattr("pr_triage.pipeline.build.OpenAICompatClient", lambda cfg: object())
    for engine in ("graph", "plain"):
        eng = _engine(BuildOptions(engine=engine, budget_pr_tokens=900_000), LlmConfig.from_env({}))
        budget = eng.steps.budget  # type: ignore[attr-defined]
        budget.record(500_000)
        assert budget.allowed()
        budget.record(500_000)
        assert not budget.allowed()
    args = cli.parser().parse_args(["run", "--base", "a", "--head", "b", "--pr", "1",
                                    "--budget-pr-tokens", "900000"])  # fmt: skip
    assert cli._opts(args, RunMode.SHADOW).budget_pr_tokens == 900_000
    assert BuildOptions().budget_pr_tokens == 200_000
