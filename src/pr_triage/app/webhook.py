"""Xác thực chữ ký webhook và chuyển sự kiện GitHub thành việc cần làm (ADR 0012 D1, D7)."""

from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass
from typing import Any

from pr_triage.core.models import JobKind

_COMMAND = re.compile(r"(?im)^\s*(fp|tp)\s+[0-9a-f]{6,12}\b")
_TRIAGE_ACTIONS = {"opened", "reopened", "synchronize", "ready_for_review"}


def verify_signature(secret: str, body: bytes, header: str | None) -> bool:
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)


@dataclass(frozen=True)
class Event:
    kind: JobKind
    repo: str
    pr_number: int
    installation_id: int
    key: str
    draft: bool = False
    sender: str = ""


def parse_event(name: str, payload: dict[str, Any], bot_login: str = "") -> Event | None:
    """None nghĩa là bỏ qua sự kiện này."""
    inst = int((payload.get("installation") or {}).get("id", 0))
    repo = (payload.get("repository") or {}).get("full_name", "")
    sender = (payload.get("sender") or {}).get("login", "")
    if not inst or not repo:
        return None
    if name == "pull_request":
        pr = payload.get("pull_request") or {}
        action = payload.get("action", "")
        number = int(pr.get("number") or payload.get("number") or 0)
        sha = (pr.get("head") or {}).get("sha", "")
        if not number or not sha:
            return None
        if action in _TRIAGE_ACTIONS:
            return Event(JobKind.TRIAGE, repo, number, inst, sha, bool(pr.get("draft")), sender)
        if action == "closed":
            return Event(
                JobKind.CLOSE, repo, number, inst, f"{sha}:{bool(pr.get('merged'))}", False, sender
            )
        return None
    if name == "issue_comment":
        issue = payload.get("issue") or {}
        comment = payload.get("comment") or {}
        sender_type = (payload.get("sender") or {}).get("type", "")
        if payload.get("action") != "created" or "pull_request" not in issue:
            return None
        if sender_type == "Bot" or (bot_login and sender.lower() == bot_login.lower()):
            return None
        if not _COMMAND.search(comment.get("body") or ""):
            return None
        return Event(
            JobKind.FEEDBACK,
            repo,
            int(issue["number"]),
            inst,
            str(comment.get("id", "")),
            False,
            sender,
        )
    return None
