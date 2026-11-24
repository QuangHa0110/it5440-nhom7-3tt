"""Hai đường kích hoạt không quét đôi một repo (ADR 0018)."""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from pr_triage.app.settings import Settings, SettingsError
from pr_triage.app.trigger import GitHubWebhookTrigger
from pr_triage.core.delivery import Channel, RepoAllowList, RepoGate, RoutePolicy
from tests.app.conftest import Env
from tests.app.fakegithub import webhook_body

ENV = {
    "GITHUB_APP_ID": "1", "GITHUB_APP_PRIVATE_KEY": "k", "GITHUB_WEBHOOK_SECRET": "w",
    "PR_TRIAGE_ALIAS_SALT": "s",
}  # fmt: skip


def payload(**kw: object) -> dict[str, object]:
    base: dict[str, object] = {
        "action": "opened", "installation": {"id": 1}, "repository": {"full_name": "o/r"},
        "number": 4, "sender": {"login": "alice"},
        "pull_request": {"number": 4, "head": {"sha": "abc123"}, "draft": False},
    }  # fmt: skip
    return {**base, **kw}


def test_webhook_trigger_makes_scan_request_for_triage_only() -> None:
    t = GitHubWebhookTrigger("bot[bot]")
    [req] = t.parse(("pull_request", payload()))
    assert (req.repo, req.pr_number, req.head_sha, req.channel) == (
        "o/r", 4, "abc123", Channel.GITHUB_APP,
    )  # fmt: skip
    assert t.parse(("pull_request", payload(action="labeled"))) == []
    assert t.parse(("pull_request", payload(action="closed"))) == []
    assert t.parse(("push", payload())) == []


def test_webhook_trigger_respects_gate() -> None:
    t = GitHubWebhookTrigger()
    gate = RepoGate(RepoAllowList.from_csv("o/*"), RoutePolicy.parse("jenkins:o/*"))
    assert t.collect(("pull_request", payload()), gate) == []
    open_gate = RepoGate(RepoAllowList.from_csv("o/*"), RoutePolicy.parse("github-app:o/*"))
    assert len(t.collect(("pull_request", payload()), open_gate)) == 1


def test_settings_routes_validated_at_startup() -> None:
    st = Settings.from_env({**ENV, "PR_TRIAGE_ROUTES": "jenkins:a/*, github-app:b/*"})
    assert st.repo_allowed("b/x") and not st.repo_allowed("a/x") and not st.repo_allowed("c/x")
    with pytest.raises(SettingsError, match="PR_TRIAGE_ROUTES"):
        Settings.from_env({**ENV, "PR_TRIAGE_ROUTES": "gitlab:a/*"})


def test_settings_default_keeps_old_behaviour() -> None:
    assert Settings.from_env(ENV).repo_allowed("anything/goes")


@pytest.fixture
def routed(tmp_path: Path) -> Iterator[Env]:
    e = Env(tmp_path, routes="jenkins:o/*, github-app:x/*")
    yield e
    e.queue.shutdown()
    e.store.close()  # Windows không xóa được thư mục tạm khi SQLite còn mở


def test_repo_routed_to_jenkins_is_ignored_by_app(routed: Env) -> None:
    r = routed.post("pull_request", webhook_body("pull_request", routed.remote))
    assert r.status_code == 200 and r.json() == {"ignored": True}
    assert routed.store.job_counts() == {}
    stats = routed.client.get("/stats", headers={"X-Admin-Token": "adm"}).json()
    assert stats["counters"]["ignored"] == 1 and stats["counters"]["queued"] == 0


def test_feedback_and_close_events_also_blocked_for_other_channel(routed: Env) -> None:
    close = webhook_body("pull_request", routed.remote, action="closed")
    assert routed.post("pull_request", close).json() == {"ignored": True}
    fb = webhook_body("issue_comment", routed.remote, action="created", comment="fp abcdef")
    assert routed.post("issue_comment", fb).json() == {"ignored": True}


def test_repo_routed_to_app_is_queued(routed: Env) -> None:
    body = webhook_body("pull_request", routed.remote, repo="x/y")
    r = routed.post("pull_request", body)
    assert r.status_code == 202
    routed.drain()
    assert json.dumps(routed.client.get("/healthz").json())
