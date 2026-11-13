"""Bộ chuyển đổi SCM cho GitHub (REST). Token lấy từ biến môi trường, không bao giờ ghi vào log."""

from __future__ import annotations

from typing import Any

import httpx

from pr_triage.core.errors import ScmError
from pr_triage.core.models import PrRef, Reaction, Reply


class GitHubScm:
    def __init__(
        self,
        token: str,
        api_url: str = "https://api.github.com",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base = api_url.rstrip("/")
        self._token = token
        self._http = httpx.Client(timeout=30, transport=transport)

    def _req(self, method: str, path: str, **kw: Any) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        resp = self._http.request(method, f"{self._base}{path}", headers=headers, **kw)
        if resp.status_code >= 400:
            text = resp.text.replace(self._token, "***") if self._token else resp.text
            raise ScmError(f"GitHub {method} {path}: HTTP {resp.status_code} {text[:200]}")
        return resp.json() if resp.content else None

    def _paged(self, path: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for page in range(1, 20):
            sep = "&" if "?" in path else "?"
            chunk = self._req("GET", f"{path}{sep}per_page=100&page={page}")
            out.extend(chunk)
            if len(chunk) < 100:
                break
        return out

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
        after = comments[ids.index(comment_ref) + 1 :]
        return [
            Reply(str(c["id"]), c["user"]["login"], c.get("body") or "", c.get("created_at", ""))
            for c in after
        ]

    def list_reactions(self, pr: PrRef, comment_ref: str) -> list[Reaction]:
        items = self._paged(f"/repos/{pr.repo}/issues/comments/{comment_ref}/reactions")
        return [
            Reaction(comment_ref, r["user"]["login"], r["content"], r.get("created_at", ""))
            for r in items
        ]

    def list_commits(self, pr: PrRef) -> list[str]:
        return [c["sha"] for c in self._paged(f"/repos/{pr.repo}/pulls/{pr.number}/commits")]

    def pr_state(self, pr: PrRef) -> str:
        data = self._req("GET", f"/repos/{pr.repo}/pulls/{pr.number}")
        if data.get("merged"):
            return "merged"
        return "closed" if data.get("state") == "closed" else "open"
