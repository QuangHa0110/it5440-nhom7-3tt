"""GitHub giả (httpx.MockTransport) và kho git cục bộ cho test của App."""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import hmac
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from tests.helpers import FIXTURE

SECRET = "webhook-secret"
NEW_CODE = """
    public String search(HttpServletRequest request, java.sql.Statement stmt) throws Exception {
        String name = request.getParameter("name");
        String q = "SELECT * FROM users WHERE name = '" + name + "'";
        return stmt.executeQuery(q).toString();
    }
}
"""


def make_keypair() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    pub = (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    return priv, pub


def sign(body: bytes, secret: str = SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def git(cwd: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-c", "user.email=t@e.org", "-c", "user.name=t", *args],
        cwd=cwd, capture_output=True, text=True, check=True,
    )  # fmt: skip
    return out.stdout.strip()


@dataclass
class Remote:
    root: Path
    base_sha: str
    head_sha: str
    merge_base: str

    @property
    def template(self) -> str:
        return str(self.root / "remotes") + "/{repo}.git"


def make_remote(tmp: Path, repo: str = "o/r", extra_commit: bool = False) -> Remote:
    """Kho nền có nhánh main và nhánh feature thêm một lỗ hổng SQL injection."""
    work = tmp / "work"
    work.mkdir()
    import shutil

    shutil.copytree(FIXTURE / "src", work / "src")
    git(work, "init", "-q", "-b", "main")
    git(work, "add", "-A")
    git(work, "commit", "-qm", "base")
    merge_base = git(work, "rev-parse", "HEAD")
    git(work, "switch", "-qc", "feature")
    c = work / "src/app/OrderController.java"
    c.write_text(c.read_text().rstrip().rstrip("}") + NEW_CODE)
    git(work, "commit", "-qam", "thêm tìm kiếm")
    head = git(work, "rev-parse", "HEAD")
    git(work, "switch", "-q", "main")
    (work / "NOTES.md").write_text("tiến triển ở nhánh đích")
    git(work, "add", "-A")
    git(work, "commit", "-qm", "main tiến lên")
    base = git(work, "rev-parse", "HEAD")
    bare = tmp / "remotes" / f"{repo}.git"
    bare.parent.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    git(work, "push", "-q", str(bare), "main", "feature")
    git(bare, "update-ref", "refs/pull/7/head", head)
    return Remote(tmp, base, head, merge_base)


@dataclass
class FakeGitHub:
    public_key: str
    remote: Remote
    repo: str = "o/r"
    number: int = 7
    author: str = "alice"
    draft: bool = False
    merged: bool = False
    state: str = "open"
    changed_files: int = 1
    files: dict[str, str] = field(default_factory=dict)  # đường dẫn -> nội dung trên nhánh đích
    comments: list[dict[str, object]] = field(default_factory=list)
    reactions: list[dict[str, object]] = field(default_factory=list)
    check_runs: list[dict[str, object]] = field(default_factory=list)
    content_refs: list[str] = field(default_factory=list)
    token_requests: int = 0
    _next: int = 100

    def head_sha(self) -> str:
        return self.remote.head_sha

    def __call__(self, req: httpx.Request) -> httpx.Response:  # noqa: C901
        path, method = req.url.path, req.method
        auth = req.headers.get("authorization", "")
        if path.startswith("/app"):
            claims = jwt.decode(auth.removeprefix("Bearer "), self.public_key, algorithms=["RS256"])
            assert claims["iss"] and claims["exp"] > claims["iat"]
            if path == "/app":
                return httpx.Response(200, json={"slug": "pr-triage-bot"})
            self.token_requests += 1
            exp = (dt.datetime.now(dt.UTC) + dt.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            return httpx.Response(201, json={"token": "ghs_faketoken", "expires_at": exp})
        assert auth == "Bearer ghs_faketoken", auth
        base = f"/repos/{self.repo}"
        if path == f"{base}/pulls/{self.number}":
            return httpx.Response(200, json={
                "state": self.state, "merged": self.merged, "draft": self.draft, "title": "t",
                "user": {"login": self.author}, "changed_files": self.changed_files,
                "base": {"ref": "main", "sha": self.remote.base_sha},
                "head": {"sha": self.head_sha(), "repo": {"full_name": "fork/r"}},
            })  # fmt: skip
        m = re.match(rf"{base}/compare/(.+)\.\.\.(.+)$", path)
        if m:
            return httpx.Response(200, json={"merge_base_commit": {"sha": self.remote.merge_base}})
        m = re.match(rf"{base}/contents/(.+)$", path)
        if m:
            self.content_refs.append(req.url.params.get("ref", ""))
            text = self.files.get(m.group(1))
            if text is None:
                return httpx.Response(404, json={"message": "Not Found"})
            return httpx.Response(200, json={
                "encoding": "base64", "content": base64.b64encode(text.encode()).decode()
            })  # fmt: skip
        if path == f"{base}/issues/{self.number}/comments":
            if method == "GET":
                page = int(req.url.params.get("page", "1"))
                return httpx.Response(200, json=self.comments if page == 1 else [])
            return self._add_comment(json.loads(req.content)["body"], "pr-triage-bot[bot]", "NONE")
        m = re.match(rf"{base}/issues/comments/(\d+)$", path)
        if m and method == "PATCH":
            for c in self.comments:
                if c["id"] == int(m.group(1)):
                    c["body"] = json.loads(req.content)["body"]
            return httpx.Response(200, json={})
        if re.match(rf"{base}/issues/comments/\d+/reactions$", path):
            return httpx.Response(200, json=self.reactions)
        if path == f"{base}/pulls/{self.number}/commits":
            return httpx.Response(200, json=[{"sha": self.head_sha()}])
        if path == f"{base}/commits/{self.head_sha()}/check-runs":
            return httpx.Response(200, json={"check_runs": self.check_runs[:1]})
        if path == f"{base}/check-runs" and method == "POST":
            body = json.loads(req.content)
            body["id"] = len(self.check_runs) + 1
            self.check_runs.append(body)
            return httpx.Response(201, json={"id": body["id"]})
        m = re.match(rf"{base}/check-runs/(\d+)$", path)
        if m and method == "PATCH":
            self.check_runs[int(m.group(1)) - 1].update(json.loads(req.content))
            return httpx.Response(200, json={})
        return httpx.Response(404, text=f"không giả lập {method} {path}")

    def _add_comment(self, body: str, login: str, assoc: str) -> httpx.Response:
        self._next += 1
        c = {"id": self._next, "body": body, "user": {"login": login}, "author_association": assoc,
             "created_at": "2026-11-14T00:00:00Z"}  # fmt: skip
        self.comments.append(c)
        return httpx.Response(201, json=c)

    def human_comment(self, body: str, login: str, assoc: str) -> None:
        self._add_comment(body, login, assoc)

    def bot_comment(self) -> str:
        return next(str(c["body"]) for c in self.comments if "pr-triage:v1" in str(c["body"]))


def webhook_body(
    event: str, remote: Remote, action: str = "opened", sender: str = "alice", repo: str = "o/r",
    number: int = 7, draft: bool = False, merged: bool = False, comment: str | None = None,
    comment_id: int = 500, sender_type: str = "User",
) -> bytes:  # fmt: skip
    payload: dict[str, object] = {
        "action": action,
        "installation": {"id": 99},
        "repository": {"full_name": repo},
        "sender": {"login": sender, "type": sender_type},
    }
    if event == "pull_request":
        payload["number"] = number
        payload["pull_request"] = {
            "number": number,
            "draft": draft,
            "merged": merged,
            "head": {"sha": remote.head_sha},
        }
    else:
        payload["issue"] = {"number": number, "pull_request": {"url": "x"}}
        payload["comment"] = {"id": comment_id, "body": comment or ""}
    return json.dumps(payload).encode()
