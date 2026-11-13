"""Chạy đầu cuối với Semgrep thật và LLM giả: kiểm tra mọi khâu nối đúng nhau."""

import json
import shutil
import sys
from pathlib import Path

import pytest

from pr_triage import cli
from pr_triage.core.models import RunStatus
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
    assert len(lines) == 1 and lines[0]["new_findings"] == 1
