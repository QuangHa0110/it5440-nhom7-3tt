import json
import re
from typing import Any

import httpx
import pytest

from pr_triage.core.errors import ScmError
from pr_triage.core.models import JobKind, PrRef
from pr_triage.core.scm import ScmKind
from pr_triage.scm.gitea import GiteaProvider
from pr_triage.scm.provider import hmac_hex
from tests.scm.helpers import FakeHost, ok, text

BASE = "https://git.example.internal"
R = "/api/v1/repos/org/repo"
REPO = "gitea:org/repo"
PULL: dict[str, Any] = {
    "number": 4, "state": "open", "merged": False, "draft": False, "title": "t",
    "user": {"login": "alice"}, "merge_base": "mb" * 20, "changed_files": 2,
    "base": {"ref": "main", "sha": "oldbase"},
    "head": {"sha": "h" * 40, "repo": {"full_name": "f/repo"}},
}  # fmt: skip


def provider(host: FakeHost) -> GiteaProvider:
    return GiteaProvider(BASE, "TOK", "sek", "pr-bot", transport=host.transport)


@pytest.fixture(autouse=True)
def fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pr_triage.scm.http.time.sleep", lambda _s: None)


def test_get_pr_then_merge_base_from_same_object() -> None:
    host = FakeHost()
    host.on("GET", rf"{R}/pulls/4", PULL)
    host.on("GET", rf"{R}/branches/main", {"commit": {"id": "tip"}})
    api = provider(host).api("TOK")
    info = api.get_pr(REPO, 4)
    assert (info.base_sha, info.head_sha, info.head_repo, info.changed_files) == (
        "tip", "h" * 40, "f/repo", 2,
    )  # fmt: skip
    assert api.merge_base(REPO, "tip", "h" * 40) == "mb" * 20
    assert host.calls[0][2]["authorization"] == "token TOK"
    with pytest.raises(ScmError):
        provider(host).api("TOK").merge_base(REPO, "x", "y")


def test_state_and_draft_mapping() -> None:
    host = FakeHost()
    host.on("GET", rf"{R}/pulls/4", {**PULL, "state": "closed", "merged": True, "draft": True})
    host.on("GET", rf"{R}/branches/main", {"commit": {"id": "tip"}})
    p = provider(host)
    info = p.api("T").get_pr(REPO, 4)
    assert (info.state, info.merged, info.draft) == ("merged", True, True)
    assert p.scm("T").pr_state(PrRef(REPO, 4)) == "merged"
    host2 = FakeHost()
    host2.on("GET", rf"{R}/pulls/4", {**PULL, "state": "closed"})
    assert provider(host2).scm("T").pr_state(PrRef(REPO, 4)) == "closed"


def test_get_file_raw_and_404() -> None:
    host = FakeHost()
    host.on("GET", rf"{R}/raw/\.pr-triage\.yml\?ref=abc", lambda *_: text("enabled: true"))
    host.on("GET", rf"{R}/raw/docs/CODEOWNERS\?ref=abc", lambda *_: ok(None, 404))
    api = provider(host).api("T")
    assert api.get_file(REPO, ".pr-triage.yml", "abc") == "enabled: true"
    assert api.get_file(REPO, "docs/CODEOWNERS", "abc") is None


def test_upsert_comment_paginates_then_updates() -> None:
    many = [{"id": i, "body": "x", "user": {"login": "u"}} for i in range(50)]
    many2 = [{"id": 99, "body": "<!--m--> cũ", "user": {"login": "bot"}}]
    host = FakeHost()
    host.on("GET", rf"{R}/issues/4/comments\?page=1&limit=50", many)
    host.on("GET", rf"{R}/issues/4/comments\?page=2&limit=50", many2)
    host.on("PATCH", rf"{R}/issues/comments/99", {"id": 99})
    scm = provider(host).scm("T")
    assert scm.upsert_comment(PrRef(REPO, 4), "<!--m-->", "<!--m--> mới") == "99"
    assert host.sent("PATCH")[0][1] == {"body": "<!--m--> mới"}
    assert host.sent("POST") == []


def test_upsert_comment_creates_when_missing() -> None:
    def create(r: httpx.Request, _m: re.Match[str]) -> httpx.Response:
        assert json.loads(r.content) == {"body": "<!--m--> a"}
        return ok({"id": 5}, 201)

    host = FakeHost()
    host.on("GET", rf"{R}/issues/4/comments\?page=1&limit=50", [])
    host.on("POST", rf"{R}/issues/4/comments", create)
    assert provider(host).scm("T").upsert_comment(PrRef(REPO, 4), "<!--m-->", "<!--m--> a") == "5"


def test_replies_roles_via_collaborators() -> None:
    comments = [
        {"id": 1, "body": "bot", "user": {"login": "bot"}},
        {"id": 2, "body": "fp abcdef1", "user": {"login": "alice"}, "created_at": "t"},
        {"id": 3, "body": "tp abcdef1", "user": {"login": "dev"}, "created_at": "t"},
        {"id": 4, "body": "hi", "user": {"login": "x"}, "created_at": "t"},
    ]
    host = FakeHost()
    host.on("GET", rf"{R}/issues/4/comments\?.*", comments)
    host.on("GET", rf"{R}/collaborators/dev", lambda *_: ok(None, 204))
    host.on("GET", rf"{R}/collaborators/x", lambda *_: ok(None, 404))
    out = provider(host).scm("T").list_replies(PrRef(REPO, 4, author="alice"), "1")
    assert [(r.comment_ref, r.role) for r in out] == [
        ("2", "author"),
        ("3", "reviewer"),
        ("4", "other"),
    ]


def test_reactions_and_commits() -> None:
    host = FakeHost()
    host.on(
        "GET", rf"{R}/issues/comments/9/reactions\?.*",
        [{"user": {"login": "alice"}, "reaction": "+1", "created": "t"}],
    )  # fmt: skip
    host.on("GET", rf"{R}/pulls/4/commits\?.*", [{"sha": "a"}, {"sha": "b"}])
    scm = provider(host).scm("T")
    pr = PrRef(REPO, 4, author="alice")
    got = scm.list_reactions(pr, "9")
    assert [(r.content, r.role, r.at) for r in got] == [("+1", "author", "t")]
    assert scm.list_commits(pr) == ["a", "b"]


def test_check_is_noop_and_remote() -> None:
    host = FakeHost()
    p = provider(host)
    assert p.scm("T").upsert_check(PrRef(REPO, 4), "n", "t", "s", []) == ""
    assert host.calls == []
    r = p.remote(REPO)
    assert (r.url, r.username, r.pr_refs(4)) == (
        f"{BASE}/org/repo.git", "pr-bot", ["refs/pull/4/head"],
    )  # fmt: skip


def test_webhook_signature_accepts_both_headers_and_rejects_bad() -> None:
    p = provider(FakeHost())
    body = b'{"a":1}'
    sig = hmac_hex("sek", body)
    assert p.verify_webhook({"x-gitea-signature": sig}, body)
    assert p.verify_webhook({"x-hub-signature-256": f"sha256={sig}"}, body)
    assert not p.verify_webhook({"x-gitea-signature": sig}, body + b" ")
    assert not p.verify_webhook({"x-hub-signature-256": sig}, body)  # thiếu tiền tố
    assert not p.verify_webhook({}, body)
    assert not GiteaProvider(BASE, "t", "").verify_webhook({"x-gitea-signature": sig}, body)


def pr_hook(action: str, **pr: Any) -> dict[str, Any]:
    return {
        "action": action, "number": 4, "repository": {"full_name": "org/repo"},
        "sender": {"login": "alice"},
        "pull_request": {"number": 4, "head": {"sha": "sha1"}, **pr},
    }  # fmt: skip


def test_parse_pull_request_events() -> None:
    p = provider(FakeHost())
    h = {"x-gitea-event": "pull_request"}
    for action in ("opened", "reopened", "synchronized"):
        ev = p.parse_webhook(h, pr_hook(action))
        assert ev is not None and (ev.kind, ev.repo, ev.key) == (JobKind.TRIAGE, REPO, "sha1")
    drafty = p.parse_webhook(h, pr_hook("opened", draft=True))
    assert drafty is not None and drafty.draft
    closed = p.parse_webhook(h, pr_hook("closed", merged=True))
    assert closed is not None and (closed.kind, closed.key) == (JobKind.CLOSE, "sha1:True")
    assert p.parse_webhook(h, pr_hook("labeled")) is None
    assert p.parse_webhook({"x-gitea-event": "push"}, pr_hook("opened")) is None


def comment_hook(body: str, sender: str = "alice", is_pull: bool = True) -> dict[str, Any]:
    return {
        "action": "created", "is_pull": is_pull, "repository": {"full_name": "org/repo"},
        "sender": {"login": sender}, "issue": {"number": 4},
        "comment": {"id": 31, "body": body},
    }  # fmt: skip


def test_parse_comment_events() -> None:
    p = provider(FakeHost())
    h = {"x-gitea-event": "issue_comment"}
    ev = p.parse_webhook(h, comment_hook("fp abcdef1"))
    assert ev is not None and (ev.kind, ev.pr_number, ev.key) == (JobKind.FEEDBACK, 4, "31")
    assert p.parse_webhook(h, comment_hook("hello")) is None
    assert p.parse_webhook(h, comment_hook("fp abcdef1", sender="PR-BOT")) is None
    assert p.parse_webhook(h, comment_hook("fp abcdef1", is_pull=False)) is None
    edited = {**comment_hook("fp abcdef1"), "action": "edited"}
    assert p.parse_webhook(h, edited) is None


def test_open_prs_and_basics() -> None:
    host = FakeHost()
    host.on(
        "GET", rf"{R}/pulls\?state=open&page=1&limit=50",
        [{"number": 8, "head": {"sha": "s"}, "base": {"ref": "dev"}, "draft": True}],
    )  # fmt: skip
    p = provider(host)
    prs = p.open_prs("T", REPO)
    assert [(x.number, x.head_sha, x.base_ref, x.draft) for x in prs] == [(8, "s", "dev", True)]
    assert p.kind is ScmKind.GITEA and p.webhook_path == "/webhook/gitea"
    with pytest.raises(ScmError):
        GiteaProvider(BASE).token()
