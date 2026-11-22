"""GitLab (REST v4): PrApiPort, ScmPort, webhook, liệt kê MR đang mở (ADR 0021)."""

from __future__ import annotations

import hmac
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
from pr_triage.scm.provider import COMMAND, Headers, ScmProvider

PAGE = 100
_REACTION_NAMES = {"thumbsup": "+1", "thumbsdown": "-1"}
_DEVELOPER = 30  # mức truy cập từ Developer trở lên coi như người xem xét


def _pid(repo: str) -> str:
    _, path = split_repo(repo)
    return urllib.parse.quote(path, safe="")


def _state(d: dict[str, Any]) -> str:
    return {"merged": "merged", "closed": "closed", "locked": "closed"}.get(d["state"], "open")


class _GitLab:
    def __init__(
        self, token: str, base_url: str, transport: httpx.BaseTransport | None, backoff_s: float
    ) -> None:
        self._c = RestClient(
            "GitLab",
            f"{base_url.rstrip('/')}/api/v4",
            lambda: {"PRIVATE-TOKEN": token},
            transport,
            backoff_s,
            (token,),
        )

    def paged(self, path: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        sep = "&" if "?" in path else "?"
        for page in range(1, MAX_PAGES):
            chunk = self._c.json("GET", f"{path}{sep}per_page={PAGE}&page={page}")
            out.extend(chunk)
            if len(chunk) < PAGE:
                break
        return out


class GitLabApi(_GitLab):
    def get_pr(self, repo: str, number: int) -> PrInfo:
        d = self._c.json("GET", f"/projects/{_pid(repo)}/merge_requests/{number}")
        branch = urllib.parse.quote(d["target_branch"], safe="")
        tip = self._c.json("GET", f"/projects/{_pid(repo)}/repository/branches/{branch}")
        return PrInfo(
            repo, number, _state(d), d["state"] == "merged",
            bool(d.get("draft") or d.get("work_in_progress")), d["author"]["username"],
            d.get("title", ""), d["target_branch"], tip["commit"]["id"], d["sha"], "",
            int(d.get("changes_count") or 0),
        )  # fmt: skip

    def merge_base(self, repo: str, base: str, head: str) -> str:
        d = self._c.json(
            "GET", f"/projects/{_pid(repo)}/repository/merge_base", params={"refs[]": [base, head]}
        )
        return str(d["id"])

    def get_file(self, repo: str, path: str, ref: str) -> str | None:
        enc = urllib.parse.quote(path, safe="")
        resp = self._c.raw(
            "GET", f"/projects/{_pid(repo)}/repository/files/{enc}/raw", params={"ref": ref}
        )
        if resp.status_code == 404:
            return None
        if resp.status_code >= 400:
            raise ScmError(f"GitLab đọc {path}: HTTP {resp.status_code}")
        return resp.text

    def open_prs(self, repo: str) -> list[OpenPr]:
        items = self.paged(f"/projects/{_pid(repo)}/merge_requests?state=opened")
        return [
            OpenPr(
                int(d["iid"]), d["sha"], d["target_branch"],
                bool(d.get("draft") or d.get("work_in_progress")),
            )
            for d in items
        ]  # fmt: skip


class GitLabScm(_GitLab):
    def __init__(
        self, token: str, base_url: str, transport: httpx.BaseTransport | None, backoff_s: float
    ) -> None:
        super().__init__(token, base_url, transport, backoff_s)
        self._roles: dict[tuple[str, int], str] = {}

    def _notes(self, pr: PrRef) -> list[dict[str, Any]]:
        path = f"/projects/{_pid(pr.repo)}/merge_requests/{pr.number}/notes"
        notes = self.paged(f"{path}?order_by=created_at&sort=asc")
        return [n for n in notes if not n.get("system")]

    def _role(self, pr: PrRef, user: dict[str, Any]) -> str:
        if pr.author and user["username"].lower() == pr.author.lower():
            return "author"
        key = (pr.repo, int(user["id"]))
        if key not in self._roles:
            resp = self._c.raw("GET", f"/projects/{_pid(pr.repo)}/members/all/{user['id']}")
            level = int(resp.json().get("access_level", 0)) if resp.status_code == 200 else 0
            self._roles[key] = "reviewer" if level >= _DEVELOPER else "other"
        return self._roles[key]

    def upsert_comment(self, pr: PrRef, marker: str, body: str) -> str:
        base = f"/projects/{_pid(pr.repo)}/merge_requests/{pr.number}/notes"
        mine = next((n for n in self._notes(pr) if marker in (n.get("body") or "")), None)
        if mine:
            self._c.json("PUT", f"{base}/{mine['id']}", json={"body": body})
            return str(mine["id"])
        return str(self._c.json("POST", base, json={"body": body})["id"])

    def list_replies(self, pr: PrRef, comment_ref: str) -> list[Reply]:
        notes = self._notes(pr)
        ids = [str(n["id"]) for n in notes]
        if comment_ref not in ids:
            return []
        out: list[Reply] = []
        for n in notes[ids.index(comment_ref) + 1 :]:
            u = n["author"]
            out.append(
                Reply(
                    str(n["id"]), u["username"], n.get("body") or "", n.get("created_at", ""),
                    self._role(pr, u),
                )
            )  # fmt: skip
        return out

    def list_reactions(self, pr: PrRef, comment_ref: str) -> list[Reaction]:
        path = f"/projects/{_pid(pr.repo)}/merge_requests/{pr.number}/notes/{comment_ref}"
        return [
            Reaction(
                comment_ref, r["user"]["username"], _REACTION_NAMES.get(r["name"], r["name"]),
                r.get("created_at", ""), self._role(pr, r["user"]),
            )
            for r in self.paged(f"{path}/award_emoji")
        ]  # fmt: skip

    def list_commits(self, pr: PrRef) -> list[str]:
        path = f"/projects/{_pid(pr.repo)}/merge_requests/{pr.number}/commits"
        return [c["id"] for c in self.paged(path)]

    def upsert_check(
        self,
        pr: PrRef,
        name: str,
        title: str,
        summary: str,
        annotations: Sequence[CheckAnnotation],
    ) -> str:
        """GitLab không có check run `neutral` kèm chú thích: bỏ qua (ADR 0021 D5)."""
        return ""

    def pr_state(self, pr: PrRef) -> str:
        return _state(self._c.json("GET", f"/projects/{_pid(pr.repo)}/merge_requests/{pr.number}"))


class GitLabProvider(ScmProvider):
    kind = ScmKind.GITLAB
    delivery_header = "x-gitlab-event-uuid"

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
            raise ScmError("GitLab: thiếu PR_TRIAGE_GITLAB_TOKEN")
        return self._token

    def api(self, token: str) -> PrApiPort:
        return GitLabApi(token, self._url, self._transport, 1.0)

    def scm(self, token: str) -> ScmPort:
        return GitLabScm(token, self._url, self._transport, 1.0)

    def remote(self, repo: str) -> GitRemote:
        _, path = split_repo(repo)
        return GitRemote(f"{self._url}/{path}.git", "oauth2", ("refs/merge-requests/{n}/head",))

    def verify_webhook(self, headers: Headers, body: bytes) -> bool:
        got = headers.get("x-gitlab-token", "")
        return bool(self._secret and got and hmac.compare_digest(self._secret, got))

    def _is_bot(self, user: str) -> bool:
        return bool(self._bot and user.lower() == self._bot.lower())

    def parse_webhook(self, headers: Headers, payload: dict[str, Any]) -> Event | None:
        name = headers.get("x-gitlab-event", "")
        path = (payload.get("project") or {}).get("path_with_namespace", "")
        sender = (payload.get("user") or {}).get("username", "")
        if not path:
            return None
        repo = join_repo(ScmKind.GITLAB, path)
        attrs = payload.get("object_attributes") or {}
        if name == "Merge Request Hook":
            number = int(attrs.get("iid") or 0)
            sha = (attrs.get("last_commit") or {}).get("id", "")
            if not number or not sha:
                return None
            action = attrs.get("action", "")
            draft = bool(attrs.get("draft") or attrs.get("work_in_progress"))
            changes = payload.get("changes") or {}
            pushed = "oldrev" in attrs or "draft" in changes
            if action in ("open", "reopen") or (action == "update" and pushed):
                return Event(JobKind.TRIAGE, repo, number, 0, sha, draft, sender)
            if action in ("close", "merge"):
                return Event(
                    JobKind.CLOSE, repo, number, 0, f"{sha}:{action == 'merge'}", False, sender
                )
            return None
        if name == "Note Hook":
            mr = payload.get("merge_request") or {}
            if attrs.get("noteable_type") != "MergeRequest" or not mr.get("iid"):
                return None
            if self._is_bot(sender) or not COMMAND.search(attrs.get("note") or ""):
                return None
            return Event(
                JobKind.FEEDBACK, repo, int(mr["iid"]), 0, str(attrs.get("id", "")), False, sender
            )
        return None

    def open_prs(self, token: str, repo: str) -> list[OpenPr]:
        return GitLabApi(token, self._url, self._transport, 1.0).open_prs(repo)
