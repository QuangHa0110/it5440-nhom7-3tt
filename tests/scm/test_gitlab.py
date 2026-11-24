import json
import re
from typing import Any

import httpx
import pytest

from pr_triage.core.errors import ScmError
from pr_triage.core.models import JobKind, PrRef
from pr_triage.core.scm import ScmKind
from pr_triage.scm.gitlab import GitLabProvider
from tests.scm.helpers import FakeHost, ok, text

BASE = "https://gl.example.internal"
API = "/api/v4/projects/grp%2Fsub%2Fproj"
REPO = "gitlab:grp/sub/proj"
MR: dict[str, Any] = {
    "iid": 5, "state": "opened", "draft": False, "title": "t",
    "author": {"username": "alice", "id": 1},
    "source_branch": "f", "target_branch": "main", "sha": "h" * 40, "changes_count": "3",
}  # fmt: skip


def provider(host: FakeHost, **kw: Any) -> GitLabProvider:
    return GitLabProvider(BASE, "TOK", "whsec", "pr-bot", transport=host.transport, **kw)


@pytest.fixture(autouse=True)
def fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pr_triage.scm.http.time.sleep", lambda _s: None)


def test_get_pr_maps_fields_and_uses_private_token() -> None:
    host = FakeHost()
    host.on("GET", rf"{API}/merge_requests/5", MR)
    host.on("GET", rf"{API}/repository/branches/main", {"commit": {"id": "b" * 40}})
    p = provider(host)
    info = p.api(p.token()).get_pr(REPO, 5)
    assert (info.repo, info.state, info.merged, info.draft, info.author) == (
        REPO, "open", False, False, "alice",
    )  # fmt: skip
    assert (info.base_ref, info.base_sha, info.head_sha, info.changed_files) == (
        "main", "b" * 40, "h" * 40, 3,
    )  # fmt: skip
    assert all(h["private-token"] == "TOK" for _m, _t, h, _b in host.calls)


@pytest.mark.parametrize(
    ("gl", "state", "merged"), [("merged", "merged", True), ("closed", "closed", False)]
)
def test_state_mapping(gl: str, state: str, merged: bool) -> None:
    host = FakeHost()
    host.on("GET", rf"{API}/merge_requests/5", {**MR, "state": gl, "work_in_progress": True})
    host.on("GET", rf"{API}/repository/branches/main", {"commit": {"id": "b"}})
    p = provider(host)
    info = p.api("TOK").get_pr(REPO, 5)
    assert (info.state, info.merged, info.draft) == (state, merged, True)
    assert p.scm("TOK").pr_state(PrRef(REPO, 5)) == state


def test_merge_base_and_get_file() -> None:
    host = FakeHost()
    host.on("GET", rf"{API}/repository/merge_base\?refs%5B%5D=aa&refs%5B%5D=bb", {"id": "mb"})
    host.on(
        "GET",
        rf"{API}/repository/files/\.pr-triage\.yml/raw\?ref=bb",
        lambda *_: text("enabled: true"),
    )
    host.on("GET", rf"{API}/repository/files/missing/raw\?ref=bb", lambda *_: ok(None, 404))
    api = provider(host).api("TOK")
    assert api.merge_base(REPO, "aa", "bb") == "mb"
    assert api.get_file(REPO, ".pr-triage.yml", "bb") == "enabled: true"
    assert api.get_file(REPO, "missing", "bb") is None


def test_file_path_is_url_encoded() -> None:
    host = FakeHost()
    host.on("GET", rf"{API}/repository/files/docs%2FCODEOWNERS/raw\?ref=x", lambda *_: text("a"))
    assert provider(host).api("T").get_file(REPO, "docs/CODEOWNERS", "x") == "a"


def test_upsert_comment_creates_then_updates_without_duplicating() -> None:
    notes: list[dict[str, Any]] = [
        {"id": 9, "body": "chuyện khác", "system": False, "author": {"username": "x", "id": 2}}
    ]

    def create(r: httpx.Request, _m: re.Match[str]) -> httpx.Response:
        n = {
            "id": 10,
            "body": json.loads(r.content)["body"],
            "system": False,
            "author": {"username": "bot", "id": 3},
        }
        notes.append(n)
        return ok(n, 201)

    def update(r: httpx.Request, m: re.Match[str]) -> httpx.Response:
        for n in notes:
            if n["id"] == int(m.group(1)):
                n["body"] = json.loads(r.content)["body"]
        return ok({"id": int(m.group(1))})

    host = FakeHost()
    host.on(
        "GET",
        rf"{API}/merge_requests/5/notes\?order_by=created_at&sort=asc&per_page=100&page=1",
        lambda *_: ok(notes),
    )
    host.on("POST", rf"{API}/merge_requests/5/notes", create)
    host.on("PUT", rf"{API}/merge_requests/5/notes/(\d+)", update)
    scm = provider(host).scm("TOK")
    pr = PrRef(REPO, 5)
    assert scm.upsert_comment(pr, "<!--m-->", "<!--m--> v1") == "10"
    assert scm.upsert_comment(pr, "<!--m-->", "<!--m--> v2") == "10"
    assert [n["body"] for n in notes] == ["chuyện khác", "<!--m--> v2"]
    assert len(host.sent("POST")) == 1 and len(host.sent("PUT")) == 1


def test_replies_skip_system_notes_and_resolve_roles() -> None:
    notes = [
        {"id": 1, "body": "bot", "system": False, "author": {"username": "bot", "id": 9}},
        {"id": 2, "body": "assigned", "system": True, "author": {"username": "s", "id": 8}},
        {
            "id": 3,
            "body": "fp abcdef1 vì...",
            "system": False,
            "created_at": "t1",
            "author": {"username": "alice", "id": 1},
        },
        {
            "id": 4,
            "body": "tp abcdef1",
            "system": False,
            "created_at": "t2",
            "author": {"username": "dev", "id": 4},
        },
        {
            "id": 5,
            "body": "hi",
            "system": False,
            "created_at": "t3",
            "author": {"username": "rando", "id": 5},
        },
    ]
    host = FakeHost()
    host.on("GET", rf"{API}/merge_requests/5/notes\?.*", notes)
    host.on("GET", rf"{API}/members/all/4", {"access_level": 30})
    host.on("GET", rf"{API}/members/all/5", lambda *_: ok(None, 404))
    out = provider(host).scm("T").list_replies(PrRef(REPO, 5, author="alice"), "1")
    assert [(r.comment_ref, r.role) for r in out] == [
        ("3", "author"),
        ("4", "reviewer"),
        ("5", "other"),
    ]
    assert provider(host).scm("T").list_replies(PrRef(REPO, 5), "404") == []


def test_reactions_are_normalised_and_commits_listed() -> None:
    host = FakeHost()
    host.on(
        "GET", rf"{API}/merge_requests/5/notes/7/award_emoji\?.*",
        [{"name": "thumbsdown", "user": {"username": "u", "id": 6}, "created_at": "t"},
         {"name": "tada", "user": {"username": "alice", "id": 1}, "created_at": "t"}],
    )  # fmt: skip
    host.on("GET", rf"{API}/members/all/6", {"access_level": 10})
    host.on("GET", rf"{API}/merge_requests/5/commits\?.*", [{"id": "c1"}, {"id": "c2"}])
    scm = provider(host).scm("T")
    pr = PrRef(REPO, 5, author="alice")
    got = scm.list_reactions(pr, "7")
    assert [(r.content, r.role) for r in got] == [("-1", "other"), ("tada", "author")]
    assert scm.list_commits(pr) == ["c1", "c2"]


def test_check_run_is_a_noop() -> None:
    host = FakeHost()
    assert provider(host).scm("T").upsert_check(PrRef(REPO, 5), "n", "t", "s", []) == ""
    assert host.calls == []


def test_error_never_leaks_token() -> None:
    host = FakeHost()
    host.on("GET", rf"{API}/merge_requests/5", lambda *_: text("bad TOK here", 400))
    with pytest.raises(ScmError) as e:
        provider(host).api("TOK").get_pr(REPO, 5)
    assert "TOK" not in str(e.value) and "400" in str(e.value)


def test_remote() -> None:
    r = provider(FakeHost()).remote(REPO)
    assert (r.url, r.username, r.pr_refs(5)) == (
        f"{BASE}/grp/sub/proj.git", "oauth2", ["refs/merge-requests/5/head"],
    )  # fmt: skip


def test_webhook_secret_is_constant_time_exact() -> None:
    p = provider(FakeHost())
    assert p.verify_webhook({"x-gitlab-token": "whsec"}, b"{}")
    assert not p.verify_webhook({"x-gitlab-token": "nope"}, b"{}")
    assert not p.verify_webhook({}, b"{}")
    assert not GitLabProvider(BASE, "t", "").verify_webhook({"x-gitlab-token": ""}, b"{}")


def mr_hook(action: str, **attrs: Any) -> dict[str, Any]:
    return {
        "project": {"path_with_namespace": "grp/sub/proj"}, "user": {"username": "alice"},
        "object_attributes": {"iid": 5, "action": action, "last_commit": {"id": "sha1"}, **attrs},
    }  # fmt: skip


def test_parse_merge_request_events() -> None:
    p = provider(FakeHost())
    h = {"x-gitlab-event": "Merge Request Hook"}
    ev = p.parse_webhook(h, mr_hook("open"))
    assert ev is not None
    assert (ev.kind, ev.repo, ev.pr_number, ev.key, ev.draft) == (
        JobKind.TRIAGE, REPO, 5, "sha1", False,
    )  # fmt: skip
    assert p.parse_webhook(h, mr_hook("update")) is None  # sửa tiêu đề, không có commit mới
    pushed = p.parse_webhook(h, mr_hook("update", oldrev="old"))
    assert pushed is not None and pushed.kind is JobKind.TRIAGE
    drafty = p.parse_webhook(h, mr_hook("open", draft=True))
    assert drafty is not None and drafty.draft
    closed = p.parse_webhook(h, mr_hook("merge"))
    assert closed is not None and (closed.kind, closed.key) == (JobKind.CLOSE, "sha1:True")
    declined = p.parse_webhook(h, mr_hook("close"))
    assert declined is not None and declined.key == "sha1:False"
    assert p.parse_webhook(h, mr_hook("approved")) is None
    assert p.parse_webhook({"x-gitlab-event": "Push Hook"}, mr_hook("open")) is None
    assert p.parse_webhook(h, {"object_attributes": {}}) is None


def note_hook(body: str, user: str = "alice", kind: str = "MergeRequest") -> dict[str, Any]:
    return {
        "project": {"path_with_namespace": "grp/sub/proj"}, "user": {"username": user},
        "object_attributes": {"noteable_type": kind, "note": body, "id": 77},
        "merge_request": {"iid": 5},
    }  # fmt: skip


def test_parse_note_events() -> None:
    p = provider(FakeHost())
    h = {"x-gitlab-event": "Note Hook"}
    ev = p.parse_webhook(h, note_hook("fp abcdef1 sai rồi"))
    assert ev is not None and (ev.kind, ev.pr_number, ev.key) == (JobKind.FEEDBACK, 5, "77")
    assert p.parse_webhook(h, note_hook("chào")) is None
    assert p.parse_webhook(h, note_hook("fp abcdef1", user="PR-Bot")) is None
    assert p.parse_webhook(h, note_hook("fp abcdef1", kind="Issue")) is None


def test_open_prs_paginates_and_maps() -> None:
    page1 = [
        {"iid": i, "sha": f"s{i}", "target_branch": "main", "draft": i == 0} for i in range(100)
    ]
    page2 = [{"iid": 500, "sha": "s500", "target_branch": "dev", "work_in_progress": False}]
    host = FakeHost()
    host.on("GET", rf"{API}/merge_requests\?state=opened&per_page=100&page=1", page1)
    host.on("GET", rf"{API}/merge_requests\?state=opened&per_page=100&page=2", page2)
    prs = provider(host).open_prs("TOK", REPO)
    assert len(prs) == 101 and prs[0].draft and prs[-1].base_ref == "dev"


def test_provider_basics() -> None:
    p = provider(FakeHost())
    assert p.kind is ScmKind.GITLAB and p.webhook_path == "/webhook/gitlab"
    with pytest.raises(ScmError):
        GitLabProvider(BASE).token()
