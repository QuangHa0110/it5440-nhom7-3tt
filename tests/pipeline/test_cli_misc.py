from pathlib import Path

import pytest

from pr_triage.cli import load_dotenv, main, parser


def test_load_dotenv_does_not_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = tmp_path / ".env"
    env.write_text("# c\nA_TEST_X=1\nB_TEST_Y='2'\nA_TEST_Z=ghi\n")
    monkeypatch.setenv("A_TEST_Z", "giu-nguyen")
    monkeypatch.delenv("A_TEST_X", raising=False)
    monkeypatch.delenv("B_TEST_Y", raising=False)
    load_dotenv(env)
    import os

    assert (os.environ["A_TEST_X"], os.environ["B_TEST_Y"], os.environ["A_TEST_Z"]) == (
        "1",
        "2",
        "giu-nguyen",
    )
    monkeypatch.delenv("A_TEST_X")
    monkeypatch.delenv("B_TEST_Y")


def test_no_command_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "usage" in capsys.readouterr().out


def test_run_requires_args() -> None:
    with pytest.raises(SystemExit):
        parser().parse_args(["run"])


def test_main_skips_dotenv_when_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    (tmp_path / ".env").write_text("PR_TRIAGE_DOTENV_PROBE=1\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PR_TRIAGE_DOTENV_PROBE", raising=False)
    monkeypatch.setenv("PR_TRIAGE_NO_DOTENV", "1")
    main([])
    assert "PR_TRIAGE_DOTENV_PROBE" not in os.environ


def test_main_loads_dotenv_by_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    (tmp_path / ".env").write_text("PR_TRIAGE_DOTENV_PROBE=1\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PR_TRIAGE_DOTENV_PROBE", raising=False)
    monkeypatch.delenv("PR_TRIAGE_NO_DOTENV", raising=False)
    main([])
    assert os.environ.get("PR_TRIAGE_DOTENV_PROBE") == "1"
    monkeypatch.delenv("PR_TRIAGE_DOTENV_PROBE")


def test_commit_time_is_utc_regardless_of_author_timezone(tmp_path: Path) -> None:
    import subprocess

    from pr_triage.pipeline.gitrepo import commit_time

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    env = {
        "GIT_COMMITTER_DATE": "2025-01-01T06:30:00+07:00",
        "GIT_AUTHOR_DATE": "2025-01-01T06:30:00+07:00",
        "PATH": __import__("os").environ["PATH"],
    }
    subprocess.run(
        ["git", "-c", "user.email=t@e.org", "-c", "user.name=t", "commit", "-q",
         "--allow-empty", "-m", "x"],
        cwd=tmp_path, env=env, check=True,
    )  # fmt: skip
    assert commit_time(tmp_path, "HEAD") == "2024-12-31T23:30:00Z"
