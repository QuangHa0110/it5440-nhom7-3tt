"""Bitbucket Server / Data Center (REST 1.0): PrApiPort, ScmPort, webhook (ADR 0021).

Webhook đã đối chiếu tài liệu chính thức (header, tên sự kiện, trường). Các đường REST còn lại
viết theo hiểu biết về API 1.0 và CHƯA đối chiếu được với trang tham chiếu (xem TD-8).
"""

from __future__ import annotations

import datetime as dt
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

LIMIT = 100
_STATES = {"OPEN": "open", "MERGED": "merged", "DECLINED": "closed"}
_TRIAGE_KEYS = {"pr:opened", "pr:from_ref_updated"}
_CLOSE_KEYS = {"pr:merged", "pr:declined", "pr:deleted"}


def _split(repo: str) -> tuple[str, str]:
    _, path = split_repo(repo)
    key, _, slug = path.partition("/")
    return key, slug


def _base(repo: str) -> str:
    key, slug = _split(repo)
    return f"/projects/{urllib.parse.quote(key)}/repos/{urllib.parse.quote(slug)}"


def _iso(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _user(u: dict[str, Any]) -> str:
    return str(u.get("slug") or u.get("name") or "")


class _Bitbucket:
    def __init__(
        self, token: str, base_url: str, transport: httpx.BaseTransport | None, backoff_s: float
    ) -> None:
        self._c = RestClient(
            "Bitbucket",
            f"{base_url.rstrip('/')}/rest/api/1.0",
            lambda: {"Authorization": f"Bearer {token}"},
            transport,
            backoff_s,
            (token,),
        )

    def values(self, path: str) -> list[dict[str, Any]]:
        """Trang kiểu Bitbucket: `values`, `isLastPage`, `nextPageStart`."""
        out: list[dict[str, Any]] = []
        sep = "&" if "?" in path else "?"
        start = 0
        for _ in range(MAX_PAGES):
            page = self._c.json("GET", f"{path}{sep}limit={LIMIT}&start={start}")
            out.extend(page.get("values", []))
            if page.get("isLastPage", True):
                break
            start = int(page["nextPageStart"])
        return out

    def pull(self, repo: str, number: int) -> dict[str, Any]:
        d: dict[str, Any] = self._c.json("GET", f"{_base(repo)}/pull-requests/{number}")
        return d


class BitbucketApi(_Bitbucket):
    def __init__(
        self, token: str, base_url: str, transport: httpx.BaseTransport | None, backoff_s: float
    ) -> None:
        super().__init__(token, base_url, transport, backoff_s)
        self._numbers: dict[tuple[str, str], int] = {}

    def get_pr(self, repo: str, number: int) -> PrInfo:
        d = self.pull(repo, number)
        base_sha, head_sha = d["toRef"]["latestCommit"], d["fromRef"]["latestCommit"]
        self._numbers[(base_sha, head_sha)] = number
        src = d["fromRef"].get("repository") or {}
        head_repo = f"{(src.get('project') or {}).get('key', '')}/{src.get('slug', '')}"
        return PrInfo(
            repo, number, _STATES.get(d["state"], "open"), d["state"] == "MERGED",
            bool(d.get("draft")), _user(d["author"]["user"]), d.get("title", ""),
            d["toRef"]["displayId"], base_sha, head_sha, head_repo.strip("/"), 0,
        )  # fmt: skip

    def merge_base(self, repo: str, base: str, head: str) -> str:
        """Cần số PR: lấy từ `get_pr` trước đó của cùng đối tượng."""
        number = self._numbers.get((base, head))
        if number is None:
            raise ScmError("Bitbucket: không biết số PR; gọi get_pr trước")
        d = self._c.json("GET", f"{_base(repo)}/pull-requests/{number}/merge-base")
        return str(d["id"])

    def get_file(self, repo: str, path: str, ref: str) -> str | None:
        enc = urllib.parse.quote(path, safe="/")
        resp = self._c.raw("GET", f"{_base(repo)}/raw/{enc}", params={"at": ref})
        if resp.status_code == 404:
            return None
        if resp.status_code >= 400:
            raise ScmError(f"Bitbucket đọc {path}: HTTP {resp.status_code}")
        return resp.text

    def open_prs(self, repo: str) -> list[OpenPr]:
        return [
            OpenPr(
                int(d["id"]), d["fromRef"]["latestCommit"], d["toRef"]["displayId"],
                bool(d.get("draft")),
            )
            for d in self.values(f"{_base(repo)}/pull-requests?state=OPEN")
        ]  # fmt: skip


class BitbucketScm(_Bitbucket):
    def _comments(self, pr: PrRef) -> list[dict[str, Any]]:
        """Mọi comment (kể cả trả lời lồng nhau), cũ nhất trước."""
        found: dict[int, dict[str, Any]] = {}

        def walk(c: dict[str, Any]) -> None:
            found[int(c["id"])] = c
            for child in c.get("comments") or []:
                walk(child)

        activities = self.values(f"{_base(pr.repo)}/pull-requests/{pr.number}/activities")
        for a in activities:
            if a.get("action") == "COMMENTED" and a.get("comment"):
                walk(a["comment"])
        return sorted(found.values(), key=lambda c: (int(c.get("createdDate", 0)), int(c["id"])))

    def upsert_comment(self, pr: PrRef, marker: str, body: str) -> str:
        base = f"{_base(pr.repo)}/pull-requests/{pr.number}/comments"
        mine = next((c for c in self._comments(pr) if marker in (c.get("text") or "")), None)
        if mine:
            payload = {"text": body, "version": mine.get("version", 0)}
            self._c.json("PUT", f"{base}/{mine['id']}", json=payload)
            return str(mine["id"])
        return str(self._c.json("POST", base, json={"text": body})["id"])

    def _reviewers(self, pr: PrRef) -> set[str]:
        d = self.pull(pr.repo, pr.number)
        return {_user(r["user"]).lower() for r in d.get("reviewers") or []}

    def list_replies(self, pr: PrRef, comment_ref: str) -> list[Reply]:
        comments = self._comments(pr)
        ids = [str(c["id"]) for c in comments]
        if comment_ref not in ids:
            return []
        reviewers = self._reviewers(pr)
        out: list[Reply] = []
        for c in comments[ids.index(comment_ref) + 1 :]:
            login = _user(c["author"])
            if pr.author and login.lower() == pr.author.lower():
                role = "author"
            else:
                role = "reviewer" if login.lower() in reviewers else "other"
            at = _iso(int(c.get("createdDate", 0)))
            out.append(Reply(str(c["id"]), login, c.get("text") or "", at, role))
        return out

    def list_reactions(self, pr: PrRef, comment_ref: str) -> list[Reaction]:
        """Bitbucket Server không có phản ứng emoji cho comment PR: phản hồi qua `fp`/`tp`."""
        return []

    def list_commits(self, pr: PrRef) -> list[str]:
        return [c["id"] for c in self.values(f"{_base(pr.repo)}/pull-requests/{pr.number}/commits")]

    def upsert_check(
        self,
        pr: PrRef,
        name: str,
        title: str,
        summary: str,
        annotations: Sequence[CheckAnnotation],
    ) -> str:
        """Không có check run `neutral` kèm chú thích: bỏ qua (ADR 0021 D5)."""
        return ""

    def pr_state(self, pr: PrRef) -> str:
        return _STATES.get(self.pull(pr.repo, pr.number)["state"], "open")


class BitbucketServerProvider(ScmProvider):
    kind = ScmKind.BITBUCKET
    delivery_header = "x-request-id"

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
            raise ScmError("Bitbucket: thiếu PR_TRIAGE_BITBUCKET_TOKEN")
        return self._token

    def api(self, token: str) -> PrApiPort:
        return BitbucketApi(token, self._url, self._transport, 1.0)

    def scm(self, token: str) -> ScmPort:
        return BitbucketScm(token, self._url, self._transport, 1.0)

    def remote(self, repo: str) -> GitRemote:
        key, slug = _split(repo)
        url = f"{self._url}/scm/{key.lower()}/{slug}.git"
        return GitRemote(url, "", ("refs/pull-requests/{n}/from",), bearer=True)

    def verify_webhook(self, headers: Headers, body: bytes) -> bool:
        return verify_hmac(self._secret, body, headers.get("x-hub-signature"), "sha256=")

    def _is_bot(self, user: str) -> bool:
        return bool(self._bot and user.lower() == self._bot.lower())

    def parse_webhook(self, headers: Headers, payload: dict[str, Any]) -> Event | None:
        key = headers.get("x-event-key", "")
        pr = payload.get("pullRequest") or {}
        number = int(pr.get("id") or 0)
        to = (pr.get("toRef") or {}).get("repository") or {}
        proj, slug = (to.get("project") or {}).get("key", ""), to.get("slug", "")
        sha = (pr.get("fromRef") or {}).get("latestCommit", "")
        if not (number and proj and slug and sha):
            return None
        repo = join_repo(ScmKind.BITBUCKET, f"{proj}/{slug}")
        actor = _user(payload.get("actor") or {})
        draft = bool(pr.get("draft"))
        if key in _TRIAGE_KEYS:
            return Event(JobKind.TRIAGE, repo, number, 0, sha, draft, actor)
        if key == "pr:modified" and payload.get("previousDraft") and not draft:
            return Event(JobKind.TRIAGE, repo, number, 0, sha, False, actor)
        if key in _CLOSE_KEYS:
            return Event(
                JobKind.CLOSE, repo, number, 0, f"{sha}:{key == 'pr:merged'}", False, actor
            )
        if key == "pr:comment:added":
            comment = payload.get("comment") or {}
            if self._is_bot(actor) or not COMMAND.search(comment.get("text") or ""):
                return None
            return Event(
                JobKind.FEEDBACK, repo, number, 0, str(comment.get("id", "")), False, actor
            )
        return None

    def open_prs(self, token: str, repo: str) -> list[OpenPr]:
        return BitbucketApi(token, self._url, self._transport, 1.0).open_prs(repo)
