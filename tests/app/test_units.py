import subprocess
import time
from pathlib import Path

import httpx
import jwt
import pytest

from pr_triage.app.auth import AppAuth
from pr_triage.app.fetcher import GitFetcher
from pr_triage.app.settings import Settings, SettingsError
from pr_triage.app.webhook import parse_event, verify_signature
from pr_triage.core.errors import ScmError
from pr_triage.core.models import JobKind
from tests.app.fakegithub import FakeGitHub, make_keypair, make_remote, sign


def test_verify_signature_edge_cases() -> None:
    body = b'{"a":1}'
    assert verify_signature("s", body, sign(body, "s"))
    assert not verify_signature("s", body, None)
    assert not verify_signature("s", body, "")
    assert not verify_signature("s", body, "sha1=abc")
    assert not verify_signature("", body, sign(body, ""))
    assert not verify_signature("s", body + b" ", sign(body, "s"))


def payload(**kw: object) -> dict[str, object]:
    base: dict[str, object] = {
        "action": "opened", "installation": {"id": 1}, "repository": {"full_name": "o/r"},
        "sender": {"login": "u", "type": "User"},
        "pull_request": {"number": 3, "draft": False, "merged": False, "head": {"sha": "abc"}},
    }  # fmt: skip
    return {**base, **kw}


def test_parse_event_matrix() -> None:
    e = parse_event("pull_request", payload())
    assert e is not None and e.kind is JobKind.TRIAGE and e.key == "abc" and e.pr_number == 3
    for action in ("reopened", "synchronize", "ready_for_review"):
        assert parse_event("pull_request", payload(action=action)) is not None
    for action in ("labeled", "edited", "assigned"):
        assert parse_event("pull_request", payload(action=action)) is None
    closed = parse_event("pull_request", payload(action="closed"))
    assert closed is not None and closed.kind is JobKind.CLOSE
    assert parse_event("pull_request", payload(installation=None)) is None
    assert parse_event("push", payload()) is None
    dependabot = payload(sender={"login": "dependabot[bot]", "type": "Bot"})
    assert parse_event("pull_request", dependabot) is not None


def comment(body: str, **kw: object) -> dict[str, object]:
    return payload(
        action="created",
        issue={"number": 3, "pull_request": {}},
        comment={"id": 9, "body": body},
        **kw,
    )


def test_parse_comment_events() -> None:
    assert parse_event("issue_comment", comment("fp abcdef trước đây"), "bot[bot]") is not None
    assert parse_event("issue_comment", comment("TP abcdef123456"), "bot[bot]") is not None
    assert parse_event("issue_comment", comment("xin chào"), "bot[bot]") is None
    assert parse_event("issue_comment", comment("fp xyz"), "bot[bot]") is None
    from_bot = comment("fp abcdef", sender={"login": "bot[bot]", "type": "User"})
    assert parse_event("issue_comment", from_bot, "bot[bot]") is None
    from_other_bot = comment("fp abcdef", sender={"login": "x[bot]", "type": "Bot"})
    assert parse_event("issue_comment", from_other_bot, "bot[bot]") is None
    issue_only = payload(
        action="created", issue={"number": 3}, comment={"id": 1, "body": "fp abcdef"}
    )
    assert parse_event("issue_comment", issue_only) is None


def test_settings_from_env_and_allowlist() -> None:
    with pytest.raises(SettingsError, match="GITHUB_APP_ID"):
        Settings.from_env({})
    env = {
        "GITHUB_APP_ID": "1", "GITHUB_APP_PRIVATE_KEY": "a\\nb", "GITHUB_WEBHOOK_SECRET": "w",
        "PR_TRIAGE_ALIAS_SALT": "s", "PR_TRIAGE_ALLOWED_REPOS": "Acme/*, other/one",
    }  # fmt: skip
    st = Settings.from_env(env)
    assert st.private_key == "a\nb" and st.workers == 2
    assert st.repo_allowed("acme/web") and st.repo_allowed("other/one")
    assert not st.repo_allowed("evil/web") and not st.repo_allowed("other/two")
    assert Settings.from_env(
        {k: v for k, v in env.items() if k != "PR_TRIAGE_ALLOWED_REPOS"}
    ).repo_allowed("x/y")
    shown = repr(st)
    assert "a\nb" not in shown and "'w'" not in shown and "'s'" not in shown


def test_settings_private_key_from_file(tmp_path: Path) -> None:
    key = tmp_path / "k.pem"
    key.write_text("PEMDATA")
    st = Settings.from_env({
        "GITHUB_APP_ID": "1", "GITHUB_APP_PRIVATE_KEY_PATH": str(key),
        "GITHUB_WEBHOOK_SECRET": "w", "PR_TRIAGE_ALIAS_SALT": "s",
    })  # fmt: skip
    assert st.private_key == "PEMDATA"


def test_auth_jwt_claims_and_token_cache(tmp_path: Path) -> None:
    priv, pub = make_keypair()
    gh = FakeGitHub(pub, make_remote(tmp_path))
    auth = AppAuth("42", priv, transport=httpx.MockTransport(gh))
    claims = jwt.decode(auth.app_jwt(), pub, algorithms=["RS256"])
    assert claims["iss"] == "42" and claims["exp"] - claims["iat"] <= 600 + 60
    assert (
        auth.installation_token(1) == "ghs_faketoken"
        and auth.installation_token(1) == "ghs_faketoken"
    )
    assert gh.token_requests == 1
    auth.installation_token(2)
    assert gh.token_requests == 2
    auth._cache[1] = ("old", time.time() + 30)
    auth.installation_token(1)
    assert gh.token_requests == 3
    assert auth.bot_login() == "pr-triage-bot[bot]"


def test_auth_error_has_no_secret() -> None:
    priv, _ = make_keypair()
    auth = AppAuth(
        "1",
        priv,
        transport=httpx.MockTransport(lambda r: httpx.Response(401, text="Bad credentials")),
    )
    with pytest.raises(ScmError) as e:
        auth.installation_token(1)
    assert "PRIVATE" not in str(e.value)


def test_fetcher_never_puts_token_in_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], dict[str, str]]] = []

    def fake_run(cmd: list[str], **kw: object) -> subprocess.CompletedProcess[str]:
        env = kw["env"]
        assert isinstance(env, dict)
        calls.append((cmd, {str(k): str(v) for k, v in env.items()}))
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with GitFetcher("https://github.com/{repo}.git").checkout(
        "o/r", "ghs_SECRET", ["a" * 40, "b" * 40], 7
    ) as path:
        assert path.name == "repo"
    assert calls
    import base64

    expected = "Authorization: Basic " + base64.b64encode(b"x-access-token:ghs_SECRET").decode()
    for cmd, env in calls:
        assert not any("ghs_SECRET" in part or "x-access-token" in part for part in cmd)
        assert env["GIT_TERMINAL_PROMPT"] == "0"
        assert env["GIT_CONFIG_COUNT"] == "1" and env["GIT_CONFIG_VALUE_0"] == expected
        assert "http.extraheader" == env["GIT_CONFIG_KEY_0"]


def test_fetcher_error_hides_token(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(cmd: list[str], **kw: object) -> subprocess.CompletedProcess[str]:
        bad = "fatal: Authentication failed for ghs_SECRET" if "fetch" in cmd else ""
        return subprocess.CompletedProcess(cmd, 1 if "fetch" in cmd else 0, "", bad)

    monkeypatch.setattr(subprocess, "run", fail)
    with pytest.raises(ScmError) as e, GitFetcher().checkout("o/r", "ghs_SECRET", ["a" * 40], 1):
        pass
    assert "ghs_SECRET" not in str(e.value)


def test_fetcher_real_local_remote_and_pull_ref_fallback(tmp_path: Path) -> None:
    remote = make_remote(tmp_path)
    f = GitFetcher(remote.template)
    with f.checkout(
        "o/r", "t", [remote.merge_base, remote.head_sha], 7, optional_shas=["f" * 40]
    ) as repo:
        out = subprocess.run(
            ["git", "cat-file", "-t", remote.head_sha],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        assert out == "commit"
        assert (repo / ".git").is_dir()
    with pytest.raises(ScmError), f.checkout("o/r", "t", ["1" * 40], 7):
        pass
