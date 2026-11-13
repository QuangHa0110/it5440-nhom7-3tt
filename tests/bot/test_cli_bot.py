import json
from pathlib import Path

import pytest

from pr_triage import cli
from pr_triage.core.models import Reply, RunMode
from pr_triage.pipeline import result_io
from pr_triage.store import SqlStore
from tests.bot.test_bot import result
from tests.fakes import FakeScm


@pytest.fixture
def result_file(tmp_path: Path) -> Path:
    r = result()
    path = tmp_path / "r.json"
    result_io.write(r, path)
    return path


def test_publish_dry_run_prints_comment_and_never_calls_scm(
    result_file: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    code = cli.main(
        [
            "publish",
            "--result",
            str(result_file),
            "--slug",
            "o/r",
            "--pr",
            "1",
            "--db",
            str(tmp_path / "s.sqlite"),
        ]
    )
    assert code == 0 and "<!-- pr-triage:v1 -->" in capsys.readouterr().out


def test_publish_post_uses_scm(
    result_file: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scm = FakeScm()
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setattr("pr_triage.cli.GitHubScm", lambda token: scm)
    code = cli.main(
        [
            "publish",
            "--result",
            str(result_file),
            "--slug",
            "o/r",
            "--pr",
            "1",
            "--db",
            str(tmp_path / "s.sqlite"),
            "--post",
        ]
    )
    assert code == 0 and len(scm.comments) == 1
    assert json.loads(capsys.readouterr().out)["mode"] == RunMode.COMMENT.value


def test_feedback_collects_and_updates_states(
    result_file: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    r = result_io.read(result_file)
    code_ = r.displayed[0].short_code
    scm = FakeScm()
    scm.replies = [Reply("1", "alice", f"fp {code_}", "t")]
    scm.state = "closed"
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    monkeypatch.setenv("PR_TRIAGE_ALIAS_SALT", "muoi")
    monkeypatch.setattr("pr_triage.cli.GitHubScm", lambda token: scm)
    db = tmp_path / "s.sqlite"
    store = SqlStore(db)
    for d in r.displayed:
        store.save_displayed(d)
    store.close()
    code = cli.main(
        [
            "feedback",
            "--result",
            str(result_file),
            "--slug",
            "o/r",
            "--pr",
            "1",
            "--comment-ref",
            "c",
            "--db",
            str(db),
        ]
    )
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["new_events"] >= 2 and out["closed"] is True
    state = SqlStore(db).list_displayed(r.run.run_id)[0].state.value
    assert state == "marked_false"


def test_feedback_requires_salt(
    result_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PR_TRIAGE_ALIAS_SALT", raising=False)
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    assert (
        cli.main(
            [
                "feedback",
                "--result",
                str(result_file),
                "--slug",
                "o/r",
                "--pr",
                "1",
                "--comment-ref",
                "c",
                "--db",
                str(tmp_path / "s.sqlite"),
            ]
        )
        == 2
    )
