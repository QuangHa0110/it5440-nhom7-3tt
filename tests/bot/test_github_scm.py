import json

import httpx
import pytest

from pr_triage.bot.github import GitHubScm
from pr_triage.core.errors import ScmError
from pr_triage.core.models import PrRef

PR = PrRef("o/r", 5)


class FakeGitHub:
    def __init__(self) -> None:
        self.comments: list[dict[str, object]] = [
            {"id": 1, "body": "người khác", "user": {"login": "x"}}
        ]
        self.log: list[tuple[str, str]] = []
        self.merged = False

    def __call__(self, req: httpx.Request) -> httpx.Response:
        assert req.headers["authorization"] == "Bearer tok"
        path, method = req.url.path, req.method
        self.log.append((method, path))
        if path == "/repos/o/r/issues/5/comments" and method == "GET":
            return httpx.Response(200, json=self.comments if req.url.params["page"] == "1" else [])
        if path == "/repos/o/r/issues/5/comments" and method == "POST":
            c = {"id": 10, "body": json.loads(req.content)["body"], "user": {"login": "bot"}}
            self.comments.append(c)
            return httpx.Response(201, json=c)
        if path.startswith("/repos/o/r/issues/comments/") and method == "PATCH":
            cid = int(path.rsplit("/", 1)[1])
            for c in self.comments:
                if c["id"] == cid:
                    c["body"] = json.loads(req.content)["body"]
            return httpx.Response(200, json={})
        if path.endswith("/reactions"):
            return httpx.Response(
                200, json=[{"user": {"login": "u"}, "content": "+1", "created_at": "t"}]
            )
        if path == "/repos/o/r/pulls/5/commits":
            return httpx.Response(200, json=[{"sha": "a"}, {"sha": "b"}])
        if path == "/repos/o/r/pulls/5":
            return httpx.Response(200, json={"state": "closed", "merged": self.merged})
        return httpx.Response(404, text="không có")


def scm(gh: FakeGitHub) -> GitHubScm:
    return GitHubScm("tok", transport=httpx.MockTransport(gh))


def test_upsert_creates_then_updates_same_comment() -> None:
    gh = FakeGitHub()
    s = scm(gh)
    ref = s.upsert_comment(PR, "<!--m-->", "<!--m--> v1")
    assert ref == "10"
    assert s.upsert_comment(PR, "<!--m-->", "<!--m--> v2") == "10"
    assert [c["body"] for c in gh.comments if c["id"] == 10] == ["<!--m--> v2"]
    assert sum(1 for m, _ in gh.log if m == "POST") == 1


def test_replies_are_comments_after_bot_comment() -> None:
    gh = FakeGitHub()
    s = scm(gh)
    s.upsert_comment(PR, "<!--m-->", "<!--m--> v1")
    gh.comments.append({"id": 11, "body": "fp abcdef", "user": {"login": "dev"}, "created_at": "t"})
    r = s.list_replies(PR, "10")
    assert [(x.author, x.body) for x in r] == [("dev", "fp abcdef")]
    assert s.list_replies(PR, "999") == []


def test_reactions_commits_state() -> None:
    gh = FakeGitHub()
    s = scm(gh)
    assert s.list_reactions(PR, "10")[0].content == "+1"
    assert s.list_commits(PR) == ["a", "b"]
    assert s.pr_state(PR) == "closed"
    gh.merged = True
    assert s.pr_state(PR) == "merged"


def test_error_hides_token() -> None:
    s = GitHubScm(
        "tok", transport=httpx.MockTransport(lambda r: httpx.Response(401, text="bad tok"))
    )
    with pytest.raises(ScmError) as e:
        s.pr_state(PR)
    assert "tok" not in str(e.value).replace("token", "")
