import json
import re
from typing import Any

import httpx
import pytest

from pr_triage.core.errors import ScmError
from pr_triage.core.models import JobKind, PrRef
from pr_triage.core.scm import ScmKind
from pr_triage.scm.bitbucket import BitbucketServerProvider
from pr_triage.scm.provider import hmac_hex
from tests.scm.helpers import FakeHost, ok, text

BASE = "https://bb.example.internal"
R = "/rest/api/1.0/projects/PROJ/repos/web"
REPO = "bitbucket:PROJ/web"
PULL: dict[str, Any] = {
    "id": 12, "state": "OPEN", "draft": False, "title": "t", "version": 3,
    "author": {"user": {"slug": "alice", "name": "alice"}},
    "fromRef": {"latestCommit": "h" * 40, "displayId": "feat",
                "repository": {"slug": "web", "project": {"key": "PROJ"}}},
    "toRef": {"latestCommit": "b" * 40, "displayId": "main"},
    "reviewers": [{"user": {"slug": "dev"}}],
}  # fmt: skip


def provider(host: FakeHost) -> BitbucketServerProvider:
    return BitbucketServerProvider(BASE, "TOK", "sek", "pr-bot", transport=host.transport)


@pytest.fixture(autouse=True)
def fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pr_triage.scm.http.time.sleep", lambda _s: None)


def test_get_pr_bearer_auth_and_merge_base() -> None:
    host = FakeHost()
    host.on("GET", rf"{R}/pull-requests/12", PULL)
    host.on("GET", rf"{R}/pull-requests/12/merge-base", {"id": "mb"})
    api = provider(host).api("TOK")
    info = api.get_pr(REPO, 12)
    assert (info.state, info.draft, info.author, info.base_ref, info.head_repo) == (
        "open", False, "alice", "main", "PROJ/web",
    )  # fmt: skip
    assert (info.base_sha, info.head_sha) == ("b" * 40, "h" * 40)
    assert api.merge_base(REPO, "b" * 40, "h" * 40) == "mb"
    assert host.calls[0][2]["authorization"] == "Bearer TOK"
    with pytest.raises(ScmError):
        provider(host).api("T").merge_base(REPO, "x", "y")


@pytest.mark.parametrize(
    ("bb", "state"), [("MERGED", "merged"), ("DECLINED", "closed"), ("OPEN", "open")]
)
def test_state_mapping(bb: str, state: str) -> None:
    host = FakeHost()
    host.on("GET", rf"{R}/pull-requests/12", {**PULL, "state": bb})
    assert provider(host).scm("T").pr_state(PrRef(REPO, 12)) == state


def test_get_file_uses_at_and_handles_404() -> None:
    host = FakeHost()
    host.on("GET", rf"{R}/raw/\.pr-triage\.yml\?at=abc", lambda *_: text("enabled: true"))
    host.on("GET", rf"{R}/raw/CODEOWNERS\?at=abc", lambda *_: ok(None, 404))
    api = provider(host).api("T")
    assert api.get_file(REPO, ".pr-triage.yml", "abc") == "enabled: true"
    assert api.get_file(REPO, "CODEOWNERS", "abc") is None


def activity(cid: int, body: str, user: str, ms: int, replies: list[Any] | None = None) -> Any:
    return {
        "action": "COMMENTED",
        "comment": {
            "id": cid, "text": body, "version": 2, "createdDate": ms,
            "author": {"slug": user}, "comments": replies or [],
        },
    }  # fmt: skip


def test_upsert_comment_pages_activities_and_updates_with_version() -> None:
    host = FakeHost()
    host.on(
        "GET", rf"{R}/pull-requests/12/activities\?limit=100&start=0",
        {"values": [{"action": "OPENED"}], "isLastPage": False, "nextPageStart": 100},
    )  # fmt: skip
    host.on(
        "GET", rf"{R}/pull-requests/12/activities\?limit=100&start=100",
        {"values": [activity(7, "<!--m--> cũ", "bot", 1)], "isLastPage": True},
    )  # fmt: skip
    host.on("PUT", rf"{R}/pull-requests/12/comments/7", {"id": 7})
    scm = provider(host).scm("T")
    assert scm.upsert_comment(PrRef(REPO, 12), "<!--m-->", "<!--m--> mới") == "7"
    assert host.sent("PUT")[0][1] == {"text": "<!--m--> mới", "version": 2}
    assert host.sent("POST") == []


def test_upsert_comment_creates_when_missing() -> None:
    def create(r: httpx.Request, _m: re.Match[str]) -> httpx.Response:
        assert json.loads(r.content) == {"text": "<!--m--> a"}
        return ok({"id": 55}, 201)

    host = FakeHost()
    host.on("GET", rf"{R}/pull-requests/12/activities\?.*", {"values": [], "isLastPage": True})
    host.on("POST", rf"{R}/pull-requests/12/comments", create)
    assert provider(host).scm("T").upsert_comment(PrRef(REPO, 12), "<!--m-->", "<!--m--> a") == "55"


def test_replies_include_nested_and_resolve_roles_oldest_first() -> None:
    nested = [activity(3, "fp abcdef1", "alice", 3000)["comment"]]
    values = [
        activity(4, "tp abcdef1", "dev", 4000),
        activity(1, "bot", "bot", 1000, replies=nested),
        activity(5, "hi", "rando", 5000),
    ]
    host = FakeHost()
    host.on("GET", rf"{R}/pull-requests/12/activities\?.*", {"values": values, "isLastPage": True})
    host.on("GET", rf"{R}/pull-requests/12", PULL)
    out = provider(host).scm("T").list_replies(PrRef(REPO, 12, author="alice"), "1")
    assert [(r.comment_ref, r.role) for r in out] == [
        ("3", "author"),
        ("4", "reviewer"),
        ("5", "other"),
    ]
    assert out[0].at == "1970-01-01T00:00:03Z"


def test_commits_reactions_check() -> None:
    host = FakeHost()
    host.on(
        "GET", rf"{R}/pull-requests/12/commits\?.*", {"values": [{"id": "c1"}], "isLastPage": True}
    )
    scm = provider(host).scm("T")
    pr = PrRef(REPO, 12)
    assert scm.list_commits(pr) == ["c1"]
    assert scm.list_reactions(pr, "1") == []
    assert scm.upsert_check(pr, "n", "t", "s", []) == ""


def test_remote_is_bearer_with_lowercase_project() -> None:
    r = provider(FakeHost()).remote(REPO)
    assert (r.url, r.bearer, r.pr_refs(12)) == (
        f"{BASE}/scm/proj/web.git", True, ["refs/pull-requests/12/from"],
    )  # fmt: skip


def test_webhook_signature() -> None:
    p = provider(FakeHost())
    body = b"{}"
    assert p.verify_webhook({"x-hub-signature": f"sha256={hmac_hex('sek', body)}"}, body)
    assert not p.verify_webhook({"x-hub-signature": hmac_hex("sek", body)}, body)
    assert not p.verify_webhook({"x-hub-signature": "sha256=00"}, body)
    assert not p.verify_webhook({}, body)


def hook(**kw: Any) -> dict[str, Any]:
    d: dict[str, Any] = {
        "actor": {"name": "alice"},
        "pullRequest": {
            "id": 12, "draft": False, "fromRef": {"latestCommit": "sha1"},
            "toRef": {"repository": {"slug": "web", "project": {"key": "PROJ"}}},
        },
    }  # fmt: skip
    d.update(kw)
    return d


def test_parse_pull_request_events() -> None:
    p = provider(FakeHost())
    for key in ("pr:opened", "pr:from_ref_updated"):
        ev = p.parse_webhook({"x-event-key": key}, hook())
        assert ev is not None and (ev.kind, ev.repo, ev.pr_number, ev.key) == (
            JobKind.TRIAGE, REPO, 12, "sha1",
        )  # fmt: skip
    merged = p.parse_webhook({"x-event-key": "pr:merged"}, hook())
    assert merged is not None and (merged.kind, merged.key) == (JobKind.CLOSE, "sha1:True")
    declined = p.parse_webhook({"x-event-key": "pr:declined"}, hook())
    assert declined is not None and declined.key == "sha1:False"
    ready = p.parse_webhook({"x-event-key": "pr:modified"}, hook(previousDraft=True))
    assert ready is not None and ready.kind is JobKind.TRIAGE
    assert p.parse_webhook({"x-event-key": "pr:modified"}, hook()) is None
    assert p.parse_webhook({"x-event-key": "repo:refs_changed"}, hook()) is None
    assert p.parse_webhook({"x-event-key": "pr:opened"}, {"pullRequest": {}}) is None


def test_parse_comment_events() -> None:
    p = provider(FakeHost())
    h = {"x-event-key": "pr:comment:added"}
    ev = p.parse_webhook(h, hook(comment={"id": 62, "text": "fp abcdef1"}))
    assert ev is not None and (ev.kind, ev.key) == (JobKind.FEEDBACK, "62")
    assert p.parse_webhook(h, hook(comment={"id": 1, "text": "chào"})) is None
    bot = hook(comment={"id": 1, "text": "fp abcdef1"}, actor={"name": "PR-Bot"})
    assert p.parse_webhook(h, bot) is None


def test_open_prs_paginate_and_basics() -> None:
    host = FakeHost()
    host.on(
        "GET", rf"{R}/pull-requests\?state=OPEN&limit=100&start=0",
        {"values": [PULL], "isLastPage": True},
    )  # fmt: skip
    p = provider(host)
    prs = p.open_prs("T", REPO)
    assert [(x.number, x.head_sha, x.base_ref) for x in prs] == [(12, "h" * 40, "main")]
    assert p.kind is ScmKind.BITBUCKET and p.webhook_path == "/webhook/bitbucket"
    with pytest.raises(ScmError):
        BitbucketServerProvider(BASE).token()
