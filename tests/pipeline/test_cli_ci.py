"""`pr-triage ci allowed|poll` (đường Jenkins, ADR 0018 D6)."""

import json
from pathlib import Path
from typing import Any

import pytest

from pr_triage import cli
from pr_triage.triggers import jenkins


@pytest.fixture(autouse=True)
def env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PR_TRIAGE_NO_DOTENV", "1")
    for k in ("PR_TRIAGE_ALLOWED_REPOS", "PR_TRIAGE_ROUTES", "GITHUB_TOKEN"):
        monkeypatch.delenv(k, raising=False)


def allowed(repo: str, pr: str = "3", *extra: str) -> int:
    return cli.main(["ci", "allowed", "--repo", repo, "--pr", pr, *extra])


def test_allowed_exit_codes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert allowed("a/b") == 1  # danh sách rỗng: không repo nào
    monkeypatch.setenv("PR_TRIAGE_ALLOWED_REPOS", "A/*")
    assert allowed("a/b") == 0
    assert allowed("x/y") == 1
    assert allowed("a/b", "abc") == 2
    assert allowed("a/b;rm", "1") == 2
    assert allowed("a/b", "1", "--head-sha", "zz") == 2
    assert "không hợp lệ" in capsys.readouterr().err


def test_allowed_honours_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PR_TRIAGE_ALLOWED_REPOS", "a/*")
    monkeypatch.setenv("PR_TRIAGE_ROUTES", "github-app:a/b, jenkins:a/c")
    assert allowed("a/b") == 1 and allowed("a/c") == 0


def test_bad_routes_exit_2(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PR_TRIAGE_ALLOWED_REPOS", "a/b")
    monkeypatch.setenv("PR_TRIAGE_ROUTES", "gitlab:a/b")
    assert allowed("a/b") == 2


def test_poll_requires_token(tmp_path: Path) -> None:
    assert cli.main(["ci", "poll", "--state", str(tmp_path / "s.json")]) == 2


def test_poll_prints_tsv_and_second_run_is_quiet(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("PR_TRIAGE_ALLOWED_REPOS", "a/b, x/*")
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    prs = [{"number": 5, "head": {"sha": "s5"}, "base": {"ref": "main"}, "draft": False}]

    def fake(url: str, token: str) -> Any:
        assert token == "tok" and "/a/b/" in url  # mẫu x/* không bị hỏi
        return prs

    monkeypatch.setattr(jenkins, "http_get_json", fake)

    state = tmp_path / "poll.json"
    assert cli.main(["ci", "poll", "--state", str(state)]) == 0
    out = capsys.readouterr()
    assert out.out == "a/b\t5\tmain\ts5\n" and "1 repo, 1 PR" in out.err
    nxt = tmp_path / "poll.json.next"
    assert json.loads(nxt.read_text()) == {"a/b#5": "s5"}
    nxt.replace(state)
    assert cli.main(["ci", "poll", "--state", str(state)]) == 0
    assert capsys.readouterr().out == ""
