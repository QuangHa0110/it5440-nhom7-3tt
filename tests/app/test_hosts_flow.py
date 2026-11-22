"""Luồng đầu cuối qua webhook cho GitLab, Gitea, Bitbucket Server (ADR 0021), kho git cục bộ."""

import json
import re
import shutil
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from pr_triage.app.fetcher import GitFetcher
from pr_triage.app.handlers import Services
from pr_triage.app.providers import HostConfig, build_host_provider
from pr_triage.app.queue import JobQueue
from pr_triage.app.server import create_app
from pr_triage.app.settings import Settings
from pr_triage.core.scm import GitRemote, ScmKind, split_repo
from pr_triage.scm.provider import ScmProvider, hmac_hex
from pr_triage.store import SqlStore
from tests.app.fakegithub import Remote, make_remote
from tests.fakes import FakeLlm
from tests.helpers import REPO_ROOT
from tests.scm.helpers import FakeHost, ok

if not (Path(sys.executable).parent / "semgrep").exists() and not shutil.which("semgrep"):
    pytest.skip("không có semgrep", allow_module_level=True)

pytestmark = pytest.mark.integration

BASE = "https://scm.example.internal"
SECRET = "whsec"


class Setup:
    """Một máy chủ giả: bảng route, kho git cục bộ, và cách dựng webhook."""

    def __init__(
        self,
        kind: ScmKind,
        repo_path: str,
        install: Callable[[FakeHost, Remote, list[str]], None],
        hook: Callable[[Remote], tuple[dict[str, str], bytes]],
    ) -> None:
        self.kind, self.repo_path, self.install, self.hook = kind, repo_path, install, hook


def _gitlab_install(host: FakeHost, r: Remote, bodies: list[str]) -> None:
    api = "/api/v4/projects/grp%2Fproj"
    host.on(
        "GET", rf"{api}/merge_requests/7",
        {"iid": 7, "state": "opened", "draft": False, "title": "t",
         "author": {"username": "alice", "id": 1}, "target_branch": "main",
         "sha": r.head_sha, "changes_count": "1"},
    )  # fmt: skip
    host.on("GET", rf"{api}/repository/branches/main", {"commit": {"id": r.base_sha}})
    host.on("GET", rf"{api}/repository/merge_base\?.*", {"id": r.merge_base})
    host.on("GET", rf"{api}/merge_requests/7/notes\?.*", lambda *_: ok(
        [{"id": 1, "body": b, "system": False, "author": {"username": "bot", "id": 9}}
         for b in bodies]
    ))  # fmt: skip

    def create(req: httpx.Request, _m: re.Match[str]) -> httpx.Response:
        bodies.append(json.loads(req.content)["body"])
        return ok({"id": 1}, 201)

    host.on("POST", rf"{api}/merge_requests/7/notes", create)


def _gitlab_hook(r: Remote) -> tuple[dict[str, str], bytes]:
    body = json.dumps({
        "project": {"path_with_namespace": "grp/proj"}, "user": {"username": "alice"},
        "object_attributes": {"iid": 7, "action": "open", "last_commit": {"id": r.head_sha}},
    }).encode()  # fmt: skip
    return {"X-Gitlab-Event": "Merge Request Hook", "X-Gitlab-Token": SECRET,
            "X-Gitlab-Event-UUID": "u1"}, body  # fmt: skip


def _gitea_install(host: FakeHost, r: Remote, bodies: list[str]) -> None:
    api = "/api/v1/repos/grp/proj"
    host.on(
        "GET", rf"{api}/pulls/7",
        {"number": 7, "state": "open", "merged": False, "draft": False, "title": "t",
         "user": {"login": "alice"}, "merge_base": r.merge_base, "changed_files": 1,
         "base": {"ref": "main", "sha": "x"}, "head": {"sha": r.head_sha}},
    )  # fmt: skip
    host.on("GET", rf"{api}/branches/main", {"commit": {"id": r.base_sha}})
    host.on("GET", rf"{api}/issues/7/comments\?.*", lambda *_: ok(
        [{"id": 1, "body": b, "user": {"login": "bot"}} for b in bodies]
    ))  # fmt: skip

    def create(req: httpx.Request, _m: re.Match[str]) -> httpx.Response:
        bodies.append(json.loads(req.content)["body"])
        return ok({"id": 1}, 201)

    host.on("POST", rf"{api}/issues/7/comments", create)


def _gitea_hook(r: Remote) -> tuple[dict[str, str], bytes]:
    body = json.dumps({
        "action": "opened", "number": 7, "repository": {"full_name": "grp/proj"},
        "sender": {"login": "alice"}, "pull_request": {"number": 7, "head": {"sha": r.head_sha}},
    }).encode()  # fmt: skip
    return {"X-Gitea-Event": "pull_request", "X-Gitea-Signature": hmac_hex(SECRET, body),
            "X-Gitea-Delivery": "d1"}, body  # fmt: skip


def _bitbucket_install(host: FakeHost, r: Remote, bodies: list[str]) -> None:
    api = "/rest/api/1.0/projects/GRP/repos/proj"
    host.on(
        "GET", rf"{api}/pull-requests/7",
        {"id": 7, "state": "OPEN", "draft": False, "title": "t",
         "author": {"user": {"slug": "alice"}},
         "fromRef": {"latestCommit": r.head_sha, "displayId": "feature"},
         "toRef": {"latestCommit": r.base_sha, "displayId": "main"}, "reviewers": []},
    )  # fmt: skip
    host.on("GET", rf"{api}/pull-requests/7/merge-base", {"id": r.merge_base})
    host.on("GET", rf"{api}/pull-requests/7/activities\?.*", lambda *_: ok({
        "values": [{"action": "COMMENTED", "comment": {"id": 1, "text": b, "version": 0,
                    "createdDate": 1, "author": {"slug": "bot"}}} for b in bodies],
        "isLastPage": True,
    }))  # fmt: skip

    def create(req: httpx.Request, _m: re.Match[str]) -> httpx.Response:
        bodies.append(json.loads(req.content)["text"])
        return ok({"id": 1}, 201)

    host.on("POST", rf"{api}/pull-requests/7/comments", create)


def _bitbucket_hook(r: Remote) -> tuple[dict[str, str], bytes]:
    body = json.dumps({
        "actor": {"name": "alice"},
        "pullRequest": {"id": 7, "draft": False, "fromRef": {"latestCommit": r.head_sha},
                        "toRef": {"repository": {"slug": "proj", "project": {"key": "GRP"}}}},
    }).encode()  # fmt: skip
    return {"X-Event-Key": "pr:opened", "X-Hub-Signature": f"sha256={hmac_hex(SECRET, body)}",
            "X-Request-Id": "r1"}, body  # fmt: skip


SETUPS = {
    "gitlab": Setup(ScmKind.GITLAB, "grp/proj", _gitlab_install, _gitlab_hook),
    "gitea": Setup(ScmKind.GITEA, "grp/proj", _gitea_install, _gitea_hook),
    "bitbucket": Setup(ScmKind.BITBUCKET, "GRP/proj", _bitbucket_install, _bitbucket_hook),
}


def local_remote(provider: ScmProvider, remote: Remote) -> Callable[[str], GitRemote]:
    """Giữ nguyên ref và cách xác thực của nhà cung cấp, chỉ đổi địa chỉ sang kho cục bộ."""
    real = provider.remote

    def build(repo: str) -> GitRemote:
        g = real(repo)
        _, path = split_repo(repo)
        url = f"{remote.root}/remotes/grp/proj.git"
        assert path.lower() == "grp/proj"
        return GitRemote(url, g.username, g.pr_ref_templates, g.bearer)

    return build


class HostEnv:
    def __init__(self, tmp: Path, name: str) -> None:
        self.setup = SETUPS[name]
        self.remote = make_remote(tmp, repo="grp/proj")
        self.bodies: list[str] = []
        self.host = FakeHost()
        self.setup.install(self.host, self.remote, self.bodies)
        cfg = HostConfig(self.setup.kind, BASE, "TOK", SECRET, "bot")
        self.provider = build_host_provider(cfg, self.host.transport)
        self.provider.remote = local_remote(self.provider, self.remote)  # type: ignore[method-assign]
        settings = Settings(
            app_id="", private_key="", webhook_secret="", alias_salt="salt", hosts=(cfg,),
            db=str(tmp / "store.sqlite"),
            rules=(str(REPO_ROOT / "configs/semgrep/java-injection.yml"),),
            catalog=str(REPO_ROOT / "configs/context/java.yml"), admin_token="adm", workers=1,
            pipeline_workers=2,
        )  # fmt: skip
        self.store = SqlStore(settings.db)
        self.services = Services(
            settings, None, self.store, GitFetcher(), FakeLlm(),  # type: ignore[arg-type]
            providers={self.setup.kind: self.provider},
        )  # fmt: skip
        self.queue = JobQueue(self.services, 1)
        self.client = TestClient(create_app(self.services, self.queue))

    def post(self, headers: dict[str, str] | None = None, body: bytes | None = None) -> Any:
        h, b = self.setup.hook(self.remote)
        return self.client.post(
            f"/webhook/{self.setup.kind.value}", content=body or b, headers=headers or h
        )


@pytest.fixture(params=sorted(SETUPS))
def henv(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[HostEnv]:
    e = HostEnv(tmp_path, request.param)
    yield e
    e.queue.shutdown()
    e.store.close()


def test_webhook_triggers_scan_and_posts_one_comment(henv: HostEnv) -> None:
    r = henv.post()
    assert r.status_code == 202, r.text
    henv.queue.wait_idle()
    job = henv.store.get_job(r.json()["queued"])
    assert job is not None and job.status.value == "done", job
    assert job.repo.startswith(f"{henv.setup.kind.value}:")
    assert len(henv.bodies) == 1 and "OrderController.java" in henv.bodies[0]
    again = henv.post()  # cùng mã giao hàng: không xếp việc thứ hai
    assert again.json() == {"duplicate": True}


def test_bad_signature_is_rejected_and_nothing_queued(henv: HostEnv) -> None:
    headers, body = henv.setup.hook(henv.remote)
    bad = {k: ("wrong" if "signature" in k.lower() or "token" in k.lower() else v)
           for k, v in headers.items()}  # fmt: skip
    assert henv.post(bad, body).status_code == 401
    assert henv.store.job_counts() == {}


def test_wrong_kind_route_and_github_route_are_not_found(henv: HostEnv) -> None:
    other = "gitea" if henv.setup.kind is not ScmKind.GITEA else "gitlab"
    assert henv.client.post(f"/webhook/{other}", content=b"{}").status_code == 404
    assert henv.client.post("/webhook", content=b"{}").status_code == 404  # GitHub tắt
    assert henv.client.post("/webhook/github", content=b"{}").status_code == 404
    assert henv.client.post("/webhook/svn", content=b"{}").status_code == 404


def test_route_policy_for_webhook_channel_blocks_other_channels(tmp_path: Path) -> None:
    e = HostEnv(tmp_path, "gitlab")
    try:
        routes = f"jenkins:{e.setup.kind.value}:grp/*"
        e.services.settings = Settings(**{**e.services.settings.__dict__, "routes": routes})
        client = TestClient(create_app(e.services, e.queue))
        h, b = e.setup.hook(e.remote)
        r = client.post("/webhook/gitlab", content=b, headers=h)
        assert r.status_code == 200 and r.json() == {"ignored": True}
        assert e.store.job_counts() == {}
    finally:
        e.queue.shutdown()
        e.store.close()
