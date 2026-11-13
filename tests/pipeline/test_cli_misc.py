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
