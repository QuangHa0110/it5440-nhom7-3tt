"""`pr-triage ci allowed|poll` (đường Jenkins, ADR 0018 D6)."""

import json
import subprocess
from pathlib import Path

import pytest

from pr_triage import cli
from pr_triage.app import providers
from pr_triage.core.scm import GitRemote, OpenPr


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


class FakeProvider:
    def __init__(self, prs: dict[str, list[OpenPr]], remote: GitRemote | None = None) -> None:
        self.prs, self._remote = prs, remote
        self.tokens_used: list[str] = []

    def token(self, installation_id: int = 0) -> str:
        return "tok"

    def open_prs(self, token: str, repo: str) -> list[OpenPr]:
        self.tokens_used.append(token)
        return self.prs[repo]

    def remote(self, repo: str) -> GitRemote:
        assert self._remote is not None
        return self._remote


def use(monkeypatch: pytest.MonkeyPatch, provider: FakeProvider) -> None:
    monkeypatch.setattr(providers, "provider_for_repo", lambda repo, env=None: provider)


def test_poll_fails_loudly_when_no_repo_could_be_asked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("PR_TRIAGE_ALLOWED_REPOS", "a/b")  # không có GITHUB_TOKEN
    assert cli.main(["ci", "poll", "--state", str(tmp_path / "s.json")]) == 2
    assert "a/b: không hỏi được" in capsys.readouterr().err


def test_poll_prints_tsv_and_second_run_is_quiet(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("PR_TRIAGE_ALLOWED_REPOS", "a/b, gitlab:g/p, x/*")
    fake = FakeProvider(
        {"a/b": [OpenPr(5, "s5", "main")], "gitlab:g/p": [OpenPr(2, "s2", "dev", draft=True)]}
    )
    use(monkeypatch, fake)
    state = tmp_path / "poll.json"
    assert cli.main(["ci", "poll", "--state", str(state)]) == 0
    out = capsys.readouterr()
    assert out.out == "a/b\t5\tmain\ts5\n" and "2 repo, 1 PR" in out.err  # mẫu x/* không bị hỏi
    assert fake.tokens_used == ["tok", "tok"]
    nxt = tmp_path / "poll.json.next"
    assert json.loads(nxt.read_text()) == {"a/b#5": "s5"}
    nxt.replace(state)
    assert cli.main(["ci", "poll", "--state", str(state)]) == 0
    assert capsys.readouterr().out == ""


def test_fetch_gets_base_and_pr_head_from_a_local_remote(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from tests.app.fakegithub import make_remote

    (tmp_path / "srv").mkdir()
    remote = make_remote(tmp_path / "srv")
    url = f"{remote.root}/remotes/o/r.git"
    subprocess.run(["git", "-C", url, "symbolic-ref", "HEAD", "refs/heads/main"], check=True)
    use(
        monkeypatch,
        FakeProvider({}, GitRemote(url, "u", ("refs/missing/{n}", "refs/pull/{n}/head"))),
    )
    dest = tmp_path / "ws"
    assert cli.main(["ci", "fetch", "--repo", "o/r", "--pr", "7", "--dest", str(dest)]) == 0
    assert json.loads(capsys.readouterr().out) == {"base": "main"}  # nhánh mặc định của repo

    def rev(ref: str) -> str:
        return subprocess.run(
            ["git", "rev-parse", ref], cwd=dest, capture_output=True, text=True, check=True
        ).stdout.strip()

    assert rev("refs/remotes/origin/pr") == remote.head_sha
    assert rev("refs/remotes/origin/base") == remote.base_sha
    # lần hai dùng lại kho đã có và nhánh đích chỉ định rõ
    assert (
        cli.main(
            ["ci", "fetch", "--repo", "o/r", "--pr", "7", "--base-ref", "main", "--dest", str(dest)]
        )
        == 0
    )


def test_fetch_reports_unreachable_remote(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    use(
        monkeypatch,
        FakeProvider({}, GitRemote(str(tmp_path / "none.git"), "u", ("refs/pull/{n}/head",))),
    )
    rc = cli.main(["ci", "fetch", "--repo", "o/r", "--pr", "7", "--base-ref", "main",
                   "--dest", str(tmp_path / "ws")])  # fmt: skip
    assert rc == 2 and "không lấy được" in capsys.readouterr().err
