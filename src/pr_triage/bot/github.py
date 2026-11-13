"""Bộ chuyển đổi GitHub (REST): ScmPort cho comment và check run, cộng các lời gọi cần cho App.

Token lấy từ chuỗi hoặc hàm cấp token (token cài đặt hết hạn), không bao giờ ghi vào log.
"""

from __future__ import annotations

import base64
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import httpx

from pr_triage.core.errors import ScmError
from pr_triage.core.models import CheckAnnotation, PrRef, Reaction, Reply

TokenSource = str | Callable[[], str]
_REVIEWER_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
_RETRY = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class PrInfo:
    repo: str
    number: int
    state: str
    merged: bool
    draft: bool
    author: str
    title: str
    base_ref: str
    base_sha: str
    head_sha: str
    head_repo: str
    changed_files: int


def role_of(login: str, association: str, pr_author: str) -> str:
    if pr_author and login.lower() == pr_author.lower():
        return "author"
    return "reviewer" if association in _REVIEWER_ASSOCIATIONS else "other"


class _Http:
    def __init__(
        self,
        token: TokenSource,
        api_url: str = "https://api.github.com",
        transport: httpx.BaseTransport | None = None,
        backoff_s: float = 1.0,
    ) -> None:
        self._base = api_url.rstrip("/")
        self._token = token
        self._http = httpx.Client(timeout=30, transport=transport)
        self._backoff = backoff_s

    def _tok(self) -> str:
        return self._token() if callable(self._token) else self._token

    def _req(self, method: str, path: str, **kw: Any) -> Any:
        last = ""
        for attempt in range(1, 4):
            token = self._tok()
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            try:
                resp = self._http.request(method, f"{self._base}{path}", headers=headers, **kw)
            except httpx.HTTPError as exc:
                last = f"{type(exc).__name__}"
            else:
                limited = resp.status_code == 403 and "rate limit" in resp.text.lower()
                if resp.status_code < 400:
                    return resp.json() if resp.content else None
                last = f"HTTP {resp.status_code} {resp.text.replace(token, '***')[:200]}"
                if resp.status_code not in _RETRY and not limited:
                    break
                wait = min(float(resp.headers.get("Retry-After", self._backoff * attempt)), 30.0)
                if attempt < 3:
                    time.sleep(wait if limited else self._backoff * attempt)
                continue
            if attempt < 3:
                time.sleep(self._backoff * attempt)
        raise ScmError(f"GitHub {method} {path}: {last}")

    def _paged(self, path: str, key: str | None = None) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for page in range(1, 20):
            sep = "&" if "?" in path else "?"
            data = self._req("GET", f"{path}{sep}per_page=100&page={page}")
            chunk = data[key] if key else data
            out.extend(chunk)
            if len(chunk) < 100:
                break
        return out


class GitHubApi(_Http):
    """Các lời gọi chỉ đọc cần cho App."""

    def get_pr(self, repo: str, number: int) -> PrInfo:
        d = self._req("GET", f"/repos/{repo}/pulls/{number}")
        head_repo = (d["head"].get("repo") or {}).get("full_name", "")
        return PrInfo(
            repo, number, d["state"], bool(d.get("merged")), bool(d.get("draft")),
            d["user"]["login"], d.get("title", ""), d["base"]["ref"], d["base"]["sha"],
            d["head"]["sha"], head_repo, int(d.get("changed_files", 0)),
        )  # fmt: skip

    def merge_base(self, repo: str, base: str, head: str) -> str:
        d = self._req("GET", f"/repos/{repo}/compare/{base}...{head}")
        return str(d["merge_base_commit"]["sha"])

    def get_file(self, repo: str, path: str, ref: str) -> str | None:
        try:
            d = self._req("GET", f"/repos/{repo}/contents/{path}?ref={ref}")
        except ScmError as exc:
            if "HTTP 404" in str(exc):
                return None
            raise
        if isinstance(d, dict) and d.get("encoding") == "base64":
            return base64.b64decode(d["content"]).decode("utf-8", "replace")
        return None


class GitHubScm(_Http):
    def upsert_comment(self, pr: PrRef, marker: str, body: str) -> str:
        comments = self._paged(f"/repos/{pr.repo}/issues/{pr.number}/comments")
        mine = next((c for c in comments if marker in (c.get("body") or "")), None)
        if mine:
            self._req(
                "PATCH", f"/repos/{pr.repo}/issues/comments/{mine['id']}", json={"body": body}
            )
            return str(mine["id"])
        created = self._req(
            "POST", f"/repos/{pr.repo}/issues/{pr.number}/comments", json={"body": body}
        )
        return str(created["id"])

    def list_replies(self, pr: PrRef, comment_ref: str) -> list[Reply]:
        """GitHub không có luồng trả lời trên comment PR: lấy mọi comment sau comment của bot."""
        comments = self._paged(f"/repos/{pr.repo}/issues/{pr.number}/comments")
        ids = [str(c["id"]) for c in comments]
        if comment_ref not in ids:
            return []
        out: list[Reply] = []
        for c in comments[ids.index(comment_ref) + 1 :]:
            login = c["user"]["login"]
            role = role_of(login, c.get("author_association", ""), pr.author)
            out.append(
                Reply(str(c["id"]), login, c.get("body") or "", c.get("created_at", ""), role)
            )
        return out

    def list_reactions(self, pr: PrRef, comment_ref: str) -> list[Reaction]:
        items = self._paged(f"/repos/{pr.repo}/issues/comments/{comment_ref}/reactions")
        return [
            Reaction(
                comment_ref, r["user"]["login"], r["content"], r.get("created_at", ""),
                role_of(r["user"]["login"], "", pr.author),
            )
            for r in items
        ]  # fmt: skip

    def list_commits(self, pr: PrRef) -> list[str]:
        return [c["sha"] for c in self._paged(f"/repos/{pr.repo}/pulls/{pr.number}/commits")]

    def upsert_check(
        self,
        pr: PrRef,
        name: str,
        title: str,
        summary: str,
        annotations: Sequence[CheckAnnotation],
    ) -> str:
        def payload(chunk: Sequence[CheckAnnotation]) -> dict[str, Any]:
            return {
                "output": {
                    "title": title[:255],
                    "summary": summary[:60000],
                    "annotations": [
                        {"path": a.path, "start_line": a.start_line, "end_line": a.end_line,
                         "annotation_level": a.level, "title": a.title[:255],
                         "message": a.message[:60000]}
                        for a in chunk
                    ],
                }
            }  # fmt: skip

        existing = self._req(
            "GET", f"/repos/{pr.repo}/commits/{pr.head_sha}/check-runs?check_name={name}"
        )
        runs = existing.get("check_runs", []) if isinstance(existing, dict) else []
        first, rest = list(annotations[:50]), list(annotations[50:])
        base = {
            "name": name,
            "head_sha": pr.head_sha,
            "status": "completed",
            "conclusion": "neutral",
        }
        if runs:
            cid = str(runs[0]["id"])
            self._req(
                "PATCH", f"/repos/{pr.repo}/check-runs/{cid}", json={**base, **payload(first)}
            )
        else:
            created = self._req(
                "POST", f"/repos/{pr.repo}/check-runs", json={**base, **payload(first)}
            )
            cid = str(created["id"])
        while rest:
            chunk, rest = rest[:50], rest[50:]
            self._req("PATCH", f"/repos/{pr.repo}/check-runs/{cid}", json=payload(chunk))
        return cid

    def pr_state(self, pr: PrRef) -> str:
        data = self._req("GET", f"/repos/{pr.repo}/pulls/{pr.number}")
        if data.get("merged"):
            return "merged"
        return "closed" if data.get("state") == "closed" else "open"
