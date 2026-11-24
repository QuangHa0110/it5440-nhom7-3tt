"""Gitea (REST v1): PrApiPort, ScmPort, webhook, liệt kê PR đang mở (ADR 0021)."""

from __future__ import annotations

import urllib.parse
from collections.abc import Sequence
from typing import Any

import httpx

from pr_triage.core.errors import ScmError
from pr_triage.core.models import CheckAnnotation, JobKind, PrRef, Reaction, Reply
from pr_triage.core.ports import ScmPort
from pr_triage.core.scm import (
    Event,
    GitRemote,
    OpenPr,
    PrApiPort,
    PrInfo,
    ScmKind,
    join_repo,
    split_repo,
)
from pr_triage.scm.http import MAX_PAGES, RestClient
from pr_triage.scm.provider import COMMAND, Headers, ScmProvider, verify_hmac

LIMIT = 50  # giá trị mặc định của MAX_RESPONSE_ITEMS trên Gitea
_TRIAGE_ACTIONS = {"opened", "reopened", "synchronized", "synchronize"}


def _path(repo: str) -> str:
    _, path = split_repo(repo)
    owner, _, name = path.partition("/")
    return f"/repos/{urllib.parse.quote(owner, safe='')}/{urllib.parse.quote(name, safe='')}"


def _state(d: dict[str, Any]) -> str:
    if d.get("merged"):
        return "merged"
    return "closed" if d.get("state") == "closed" else "open"


class _Gitea:
    def __init__(
        self, token: str, base_url: str, transport: httpx.BaseTransport | None, backoff_s: float
    ) -> None:
        self._c = RestClient(
            "Gitea",
            f"{base_url.rstrip('/')}/api/v1",
            lambda: {"Authorization": f"token {token}"},
            transport,
            backoff_s,
            (token,),
        )

    def paged(self, path: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        sep = "&" if "?" in path else "?"
        for page in range(1, MAX_PAGES):
            chunk = self._c.json("GET", f"{path}{sep}page={page}&limit={LIMIT}")
            if chunk is None:
                break
            out.extend(chunk)
            if len(chunk) < LIMIT:
                break
        return out


class GiteaApi(_Gitea):
    def __init__(
        self, token: str, base_url: str, transport: httpx.BaseTransport | None, backoff_s: float
    ) -> None:
        super().__init__(token, base_url, transport, backoff_s)
        self._merge_bases: dict[tuple[str, str], str] = {}

    def get_pr(self, repo: str, number: int) -> PrInfo:
        d = self._c.json("GET", f"{_path(repo)}/pulls/{number}")
        base_ref = d["base"]["ref"]
        branch = urllib.parse.quote(base_ref, safe="")
        tip = self._c.json("GET", f"{_path(repo)}/branches/{branch}")["commit"]["id"]
        head_sha = d["head"]["sha"]
        if d.get("merge_base"):
            self._merge_bases[(tip, head_sha)] = d["merge_base"]
        return PrInfo(
            repo, number, _state(d), bool(d.get("merged")), bool(d.get("draft")),
            d["user"]["login"], d.get("title", ""), base_ref, tip, head_sha,
            (d["head"].get("repo") or {}).get("full_name", ""),
            int(d.get("changed_files") or 0),
        )  # fmt: skip

    def merge_base(self, repo: str, base: str, head: str) -> str:
        """Gitea đưa `merge_base` trong chính PR: phải gọi `get_pr` trước, cùng một đối tượng."""
        try:
            return self._merge_bases[(base, head)]
        except KeyError:
            raise ScmError("Gitea: không có merge_base; gọi get_pr trước") from None

    def get_file(self, repo: str, path: str, ref: str) -> str | None:
        enc = urllib.parse.quote(path, safe="/")
        resp = self._c.raw("GET", f"{_path(repo)}/raw/{enc}", params={"ref": ref})
        if resp.status_code == 404:
            return None
        if resp.status_code >= 400:
            raise ScmError(f"Gitea đọc {path}: HTTP {resp.status_code}")
        return resp.text

    def open_prs(self, repo: str) -> list[OpenPr]:
        return [
            OpenPr(int(d["number"]), d["head"]["sha"], d["base"]["ref"], bool(d.get("draft")))
            for d in self.paged(f"{_path(repo)}/pulls?state=open")
        ]


class GiteaScm(_Gitea):
    def __init__(
        self, token: str, base_url: str, transport: httpx.BaseTransport | None, backoff_s: float
    ) -> None:
        super().__init__(token, base_url, transport, backoff_s)
        self._roles: dict[tuple[str, str], str] = {}

    def _role(self, pr: PrRef, login: str) -> str:
        if pr.author and login.lower() == pr.author.lower():
            return "author"
        key = (pr.repo, login.lower())
        if key not in self._roles:
            resp = self._c.raw("GET", f"{_path(pr.repo)}/collaborators/{urllib.parse.quote(login)}")
            self._roles[key] = "reviewer" if resp.status_code == 204 else "other"
        return self._roles[key]

    def _comments(self, pr: PrRef) -> list[dict[str, Any]]:
        return self.paged(f"{_path(pr.repo)}/issues/{pr.number}/comments")

    def upsert_comment(self, pr: PrRef, marker: str, body: str) -> str:
        mine = next((c for c in self._comments(pr) if marker in (c.get("body") or "")), None)
        if mine:
            self._c.json(
                "PATCH", f"{_path(pr.repo)}/issues/comments/{mine['id']}", json={"body": body}
            )
            return str(mine["id"])
        created = self._c.json(
            "POST", f"{_path(pr.repo)}/issues/{pr.number}/comments", json={"body": body}
        )
        return str(created["id"])

    def list_replies(self, pr: PrRef, comment_ref: str) -> list[Reply]:
        comments = self._comments(pr)
        ids = [str(c["id"]) for c in comments]
        if comment_ref not in ids:
            return []
        out: list[Reply] = []
        for c in comments[ids.index(comment_ref) + 1 :]:
            login = c["user"]["login"]
            out.append(
                Reply(
                    str(c["id"]), login, c.get("body") or "", c.get("created_at", ""),
                    self._role(pr, login),
                )
            )  # fmt: skip
        return out

    def list_reactions(self, pr: PrRef, comment_ref: str) -> list[Reaction]:
        items = self.paged(f"{_path(pr.repo)}/issues/comments/{comment_ref}/reactions")
        return [
            Reaction(
                comment_ref, r["user"]["login"], r["reaction"],
                r.get("created", r.get("created_at", "")),
                self._role(pr, r["user"]["login"]),
            )
            for r in items
        ]  # fmt: skip

    def list_commits(self, pr: PrRef) -> list[str]:
        return [c["sha"] for c in self.paged(f"{_path(pr.repo)}/pulls/{pr.number}/commits")]

    def upsert_check(
        self,
        pr: PrRef,
        name: str,
        title: str,
        summary: str,
        annotations: Sequence[CheckAnnotation],
    ) -> str:
        """Gitea không có check run `neutral` kèm chú thích: bỏ qua (ADR 0021 D5)."""
        return ""

    def pr_state(self, pr: PrRef) -> str:
        return _state(self._c.json("GET", f"{_path(pr.repo)}/pulls/{pr.number}"))


class GiteaProvider(ScmProvider):
    kind = ScmKind.GITEA
    delivery_header = "x-gitea-delivery"

    def __init__(
        self,
        base_url: str,
        token: str = "",
        webhook_secret: str = "",
        bot: str = "",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._url = base_url.rstrip("/")
        self._token = token
        self._secret = webhook_secret
        self._bot = bot
        self._transport = transport

    def bot_login(self) -> str:
        return self._bot

    def token(self, installation_id: int = 0) -> str:
        if not self._token:
            raise ScmError("Gitea: thiếu PR_TRIAGE_GITEA_TOKEN")
        return self._token

    def api(self, token: str) -> PrApiPort:
        return GiteaApi(token, self._url, self._transport, 1.0)

    def scm(self, token: str) -> ScmPort:
        return GiteaScm(token, self._url, self._transport, 1.0)

    def remote(self, repo: str) -> GitRemote:
        _, path = split_repo(repo)
        return GitRemote(f"{self._url}/{path}.git", self._bot or "oauth2", ("refs/pull/{n}/head",))

    def verify_webhook(self, headers: Headers, body: bytes) -> bool:
        plain = headers.get("x-gitea-signature")
        if plain:
            return verify_hmac(self._secret, body, plain)
        return verify_hmac(self._secret, body, headers.get("x-hub-signature-256"), "sha256=")

    def _is_bot(self, user: str) -> bool:
        return bool(self._bot and user.lower() == self._bot.lower())

    def parse_webhook(self, headers: Headers, payload: dict[str, Any]) -> Event | None:
        name = headers.get("x-gitea-event", "")
        full = (payload.get("repository") or {}).get("full_name", "")
        sender = (payload.get("sender") or {}).get("login", "")
        if not full:
            return None
        repo = join_repo(ScmKind.GITEA, full)
        if name == "pull_request":
            pr = payload.get("pull_request") or {}
            number = int(pr.get("number") or payload.get("number") or 0)
            sha = (pr.get("head") or {}).get("sha", "")
            action = payload.get("action", "")
            if not number or not sha:
                return None
            if action in _TRIAGE_ACTIONS:
                return Event(JobKind.TRIAGE, repo, number, 0, sha, bool(pr.get("draft")), sender)
            if action == "closed":
                merged = bool(pr.get("merged"))
                return Event(JobKind.CLOSE, repo, number, 0, f"{sha}:{merged}", False, sender)
            return None
        if name in ("issue_comment", "pull_request_comment"):
            issue = payload.get("issue") or {}
            comment = payload.get("comment") or {}
            is_pr = bool(payload.get("is_pull") or issue.get("pull_request"))
            if payload.get("action") != "created" or not is_pr or not issue.get("number"):
                return None
            if self._is_bot(sender) or not COMMAND.search(comment.get("body") or ""):
                return None
            key = str(comment.get("id", ""))
            return Event(JobKind.FEEDBACK, repo, int(issue["number"]), 0, key, False, sender)
        return None

    def open_prs(self, token: str, repo: str) -> list[OpenPr]:
        return GiteaApi(token, self._url, self._transport, 1.0).open_prs(repo)
