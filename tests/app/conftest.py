import shutil
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from pr_triage.app.auth import AppAuth
from pr_triage.app.fetcher import GitFetcher
from pr_triage.app.handlers import Services
from pr_triage.app.queue import JobQueue
from pr_triage.app.server import create_app
from pr_triage.app.settings import Settings
from pr_triage.store import SqlStore
from tests.app.fakegithub import FakeGitHub, Remote, make_keypair, make_remote
from tests.fakes import FakeLlm
from tests.helpers import REPO_ROOT

if not (Path(sys.executable).parent / "semgrep").exists() and not shutil.which("semgrep"):
    pytest.skip("không có semgrep", allow_module_level=True)

pytestmark = pytest.mark.integration


class Env:
    def __init__(self, tmp: Path, llm: object | None = None, **settings: object) -> None:
        self.priv, pub = make_keypair()
        self.remote: Remote = make_remote(tmp)
        self.gh = FakeGitHub(pub, self.remote)
        transport = httpx.MockTransport(self.gh)
        base = dict(
            app_id="123", private_key=self.priv, webhook_secret="webhook-secret", alias_salt="salt",
            git_url_template=self.remote.template, db=str(tmp / "store.sqlite"),
            rules=(str(REPO_ROOT / "configs/semgrep/java-injection.yml"),),
            catalog=str(REPO_ROOT / "configs/context/java.yml"), admin_token="adm", workers=1,
            pipeline_workers=2,
        )  # fmt: skip
        self.settings = Settings(**{**base, **settings})  # type: ignore[arg-type]
        self.store = SqlStore(self.settings.db)
        self.llm = llm or FakeLlm()
        self.services = Services(
            self.settings,
            AppAuth("123", self.priv, transport=transport),
            self.store,
            GitFetcher(self.settings.git_url_template),
            self.llm,  # type: ignore[arg-type]
            transport,
        )
        self.queue = JobQueue(self.services, 1)
        self.app = create_app(self.services, self.queue)
        self.client = TestClient(self.app)

    def post(
        self, event: str, body: bytes, signature: str | None = None, delivery: str = "d1"
    ) -> Any:
        from tests.app.fakegithub import sign

        headers = {
            "X-GitHub-Event": event, "X-GitHub-Delivery": delivery,
            "X-Hub-Signature-256": signature if signature is not None else sign(body),
            "Content-Type": "application/json",
        }  # fmt: skip
        return self.client.post("/webhook", content=body, headers=headers)

    def drain(self) -> None:
        self.queue.wait_idle()


@pytest.fixture
def env(tmp_path: Path) -> Iterator[Env]:
    e = Env(tmp_path)
    yield e
    e.queue.shutdown()
