import json
from pathlib import Path

from pr_triage.core.models import AlertState, ContextBundle, Finding, Verdict, VerdictLabel
from tests.app.conftest import Env
from tests.app.fakegithub import SECRET, sign, webhook_body

MARK = "<!-- pr-triage:v1 -->"


def test_signature_ping_and_ignored_events(env: Env) -> None:
    body = webhook_body("pull_request", env.remote)
    assert env.post("pull_request", body, signature="sha256=deadbeef").status_code == 401
    assert env.post("pull_request", body, signature="").status_code == 401
    assert env.post("pull_request", body, signature=sign(body, "sai-secret")).status_code == 401
    assert env.post("ping", b"{}").json() == {"pong": True}
    labeled = webhook_body("pull_request", env.remote, action="labeled")
    assert env.post("pull_request", labeled).json() == {"ignored": True}
    other = webhook_body("pull_request", env.remote, repo="x/y")
    assert env.post("pull_request", other).status_code == 202
    assert (
        env.post("pull_request", b"khong-phai-json", signature=sign(b"khong-phai-json")).status_code
        == 400
    )
    assert SECRET not in json.dumps(env.client.get("/healthz").json())


def test_oversized_body_rejected(env: Env) -> None:
    big = b"x" * (env.settings.max_body_bytes + 1)
    assert env.post("pull_request", big).status_code == 413


def test_pull_request_gets_one_comment_and_one_neutral_check(env: Env) -> None:
    r = env.post("pull_request", webhook_body("pull_request", env.remote))
    assert r.status_code == 202
    env.drain()
    job = env.store.get_job(r.json()["queued"])
    assert job is not None and job.status.value == "done", job
    body = env.gh.bot_comment()
    assert "OrderController.java" in body and "cảnh báo cần xem" in body and "fp <mã>" in body
    assert "không có nghĩa là mã an toàn" in body
    assert len(env.gh.check_runs) == 1
    check = env.gh.check_runs[0]
    assert check["conclusion"] == "neutral" and check["head_sha"] == env.remote.head_sha
    assert any(a["path"] == "src/app/OrderController.java" for a in check["output"]["annotations"])  # type: ignore[index]
    run = env.store.latest_run_with_comment("o/r", 7)
    assert (
        run is not None
        and run[0].head_sha == env.remote.head_sha
        and run[0].mode.value == "comment"
    )
    assert run[0].base_sha == env.remote.merge_base


def test_redelivery_and_same_head_are_not_reprocessed(env: Env) -> None:
    body = webhook_body("pull_request", env.remote)
    assert env.post("pull_request", body, delivery="same").status_code == 202
    env.drain()
    assert env.post("pull_request", body, delivery="same").json() == {"duplicate": True}
    sync = webhook_body("pull_request", env.remote, action="synchronize")
    assert env.post("pull_request", sync, delivery="other").json() == {"duplicate": True}
    env.drain()
    assert len([c for c in env.gh.comments if MARK in str(c["body"])]) == 1


def test_config_is_read_from_base_branch_only(env: Env) -> None:
    env.gh.files[".pr-triage.yml"] = "enabled: false\n"
    r = env.post("pull_request", webhook_body("pull_request", env.remote))
    env.drain()
    job = env.store.get_job(r.json()["queued"])
    assert job is not None and job.status.value == "skipped" and "tắt" in job.error
    assert env.gh.comments == [] and env.gh.check_runs == []
    assert env.gh.content_refs and set(env.gh.content_refs) == {env.remote.base_sha}


def test_invalid_config_is_reported_in_the_pr(env: Env) -> None:
    env.gh.files[".pr-triage.yml"] = "mode: chặn-merge\nlạ: 1\n"
    r = env.post("pull_request", webhook_body("pull_request", env.remote))
    env.drain()
    job = env.store.get_job(r.json()["queued"])
    assert job is not None and job.status.value == "failed"
    body = env.gh.bot_comment()
    assert (
        "cấu hình `.pr-triage.yml` sai" in body
        and "mode:" in body
        and "lạ: khóa không được hỗ trợ" in body
    )


def test_shadow_mode_posts_nothing_but_stores_results(env: Env) -> None:
    env.gh.files[".pr-triage.yml"] = "mode: shadow\n"
    r = env.post("pull_request", webhook_body("pull_request", env.remote))
    env.drain()
    job = env.store.get_job(r.json()["queued"])
    assert job is not None and job.status.value == "done"
    assert env.gh.comments == [] and env.gh.check_runs == []
    assert [run.mode.value for run in env.store.list_runs()] == ["shadow"]


def test_draft_too_large_and_disabled_check_run(env: Env) -> None:
    draft = webhook_body("pull_request", env.remote, draft=True)
    assert env.post("pull_request", draft).json() == {"ignored": "PR nháp"}
    env.gh.changed_files = 5
    env.gh.files[".pr-triage.yml"] = "limits: {max_changed_files: 2}\n"
    r = env.post("pull_request", webhook_body("pull_request", env.remote), delivery="big")
    env.drain()
    job = env.store.get_job(r.json()["queued"])
    assert job is not None and job.status.value == "skipped"
    assert (
        "quá lớn" in env.gh.bot_comment() and "không có nghĩa là mã an toàn" in env.gh.bot_comment()
    )


def test_check_run_can_be_disabled(env: Env) -> None:
    env.gh.files[".pr-triage.yml"] = "check_run: {enabled: false}\n"
    env.post("pull_request", webhook_body("pull_request", env.remote))
    env.drain()
    assert env.gh.check_runs == [] and "OrderController.java" in env.gh.bot_comment()


def test_cc_author_when_configured_and_never_from_model(env: Env) -> None:
    class Evil:
        def triage(self, f: Finding, b: ContextBundle) -> Verdict:
            return Verdict(
                "v", f.finding_id, b.variant, "m", "p", VerdictLabel.LIKELY_TRUE,
                explanation="Gọi @victim ngay <img src=x> https://evil.example",
            )  # fmt: skip

    env.services.llm = Evil()
    env.gh.files[".pr-triage.yml"] = "mentions: {mode: [author], min_severity: high}\n"
    env.post("pull_request", webhook_body("pull_request", env.remote))
    env.drain()
    body = env.gh.bot_comment()
    assert "cc @alice" in body
    assert "@victim" not in body and "<img" not in body and "https://evil" not in body
    assert "@​victim" in body


def test_fp_reply_by_reviewer_marks_alert_false_author_does_not_when_untrusted(env: Env) -> None:
    env.gh.files[".pr-triage.yml"] = "feedback: {trusted_roles: [reviewer]}\n"
    env.post("pull_request", webhook_body("pull_request", env.remote))
    env.drain()
    code = env.store.list_displayed(env.store.list_runs()[0].run_id)[0].short_code
    env.gh.human_comment(f"fp {code} tôi tự thấy ổn", "alice", "CONTRIBUTOR")
    cmt = webhook_body(
        "issue_comment", env.remote, action="created", comment=f"fp {code}", comment_id=501
    )
    assert env.post("issue_comment", cmt, delivery="c1").status_code == 202
    env.drain()
    run_id = env.store.list_runs()[0].run_id
    assert env.store.list_displayed(run_id)[0].state is AlertState.RESPONDED
    env.gh.human_comment(f"fp {code} đã kiểm tra, đúng là sai", "bob", "MEMBER")
    cmt2 = webhook_body(
        "issue_comment",
        env.remote,
        action="created",
        comment=f"fp {code}",
        comment_id=502,
        sender="bob",
    )
    env.post("issue_comment", cmt2, delivery="c2")
    env.drain()
    assert env.store.list_displayed(run_id)[0].state is AlertState.MARKED_FALSE
    roles = {e.actor_role for e in env.store.list_feedback(run_id) if e.kind.value == "reply_fp"}
    assert roles == {"author", "reviewer"}


def test_bot_comments_and_plain_comments_are_ignored(env: Env) -> None:
    bot = webhook_body(
        "issue_comment",
        env.remote,
        action="created",
        comment="fp abcdef",
        sender="x[bot]",
        sender_type="Bot",
    )
    assert env.post("issue_comment", bot).json() == {"ignored": True}
    plain = webhook_body("issue_comment", env.remote, action="created", comment="cảm ơn bot")
    assert env.post("issue_comment", plain, delivery="p").json() == {"ignored": True}
    edited = webhook_body("issue_comment", env.remote, action="edited", comment="fp abcdef")
    assert env.post("issue_comment", edited, delivery="e").json() == {"ignored": True}


def test_closing_pr_without_feedback_marks_alerts_ignored(env: Env) -> None:
    env.post("pull_request", webhook_body("pull_request", env.remote))
    env.drain()
    env.gh.state, env.gh.merged = "closed", True
    r = env.post(
        "pull_request",
        webhook_body("pull_request", env.remote, action="closed", merged=True),
        delivery="cl",
    )
    assert r.status_code == 202
    env.drain()
    run_id = env.store.list_runs()[0].run_id
    assert [a.state for a in env.store.list_displayed(run_id)] == [AlertState.IGNORED]
    assert any(e.kind.value == "merge" for e in env.store.list_feedback(run_id))


def test_stale_job_when_pr_has_new_head_is_skipped(env: Env) -> None:
    body = webhook_body("pull_request", env.remote)
    payload = json.loads(body)
    payload["pull_request"]["head"]["sha"] = "0" * 40
    stale = json.dumps(payload).encode()
    r = env.post("pull_request", stale, delivery="stale")
    env.drain()
    job = env.store.get_job(r.json()["queued"])
    assert job is not None and job.status.value == "skipped" and "mới hơn" in job.error
    assert env.gh.comments == []


def test_new_commit_marks_previous_alert_fixed(env: Env) -> None:
    import subprocess

    env.post("pull_request", webhook_body("pull_request", env.remote))
    env.drain()
    first = env.store.list_runs()[0]
    # tác giả sửa lỗ hổng: commit mới trên feature
    from tests.app.fakegithub import git

    work = env.remote.root / "work"
    git(work, "switch", "-q", "feature")
    c = work / "src/app/OrderController.java"
    c.write_text(
        c.read_text().replace('"SELECT * FROM users WHERE name = \'" + name + "\'"', '"SELECT 1"')
    )
    git(work, "commit", "-qam", "sửa lỗ hổng")
    new_head = git(work, "rev-parse", "HEAD")
    bare = env.remote.root / "remotes/o/r.git"
    subprocess.run(["git", "push", "-q", str(bare), "feature"], cwd=work, check=True)
    env.remote.head_sha = new_head
    env.post(
        "pull_request", webhook_body("pull_request", env.remote, action="synchronize"), delivery="n"
    )
    env.drain()
    assert [a.state for a in env.store.list_displayed(first.run_id)] == [AlertState.FIXED]
    assert len(env.store.list_runs()) == 2
    assert (
        "không có cảnh báo mới" in env.gh.bot_comment().lower()
        or "OrderController" not in env.gh.bot_comment()
    )


def test_resume_runs_jobs_left_queued_after_restart(env: Env) -> None:
    from pr_triage.core.models import Job, JobKind

    job = Job(JobKind.TRIAGE, "o/r", 7, 99, env.remote.head_sha, "left-over")
    saved = env.store.enqueue_job(job)
    assert saved is not None and saved.status.value == "queued"
    assert env.queue.resume() == 1
    env.drain()
    done = env.store.get_job(saved.job_id)
    assert done is not None and done.status.value == "done" and done.attempts == 1


def test_ops_endpoints_require_admin_token(env: Env) -> None:
    assert env.client.get("/healthz").json() == {"status": "ok"}
    assert env.client.get("/readyz").json() == {"status": "ready"}
    assert env.client.get("/stats").status_code == 404
    assert env.client.get("/metrics", headers={"X-Admin-Token": "sai"}).status_code == 404
    env.post("pull_request", webhook_body("pull_request", env.remote))
    env.drain()
    stats = env.client.get("/stats", headers={"X-Admin-Token": "adm"}).json()
    assert stats["jobs"] == {"done": 1} and stats["counters"]["queued"] == 1
    assert stats["recent"][0]["repo"] == "o/r"
    metrics = env.client.get("/metrics", headers={"X-Admin-Token": "adm"}).text
    assert 'pr_triage_jobs{status="done"} 1' in metrics and "pr_triage_webhooks_queued 1" in metrics
    assert "ghs_" not in metrics and "adm" not in metrics.replace("admin", "")


def test_admin_endpoints_hidden_when_no_token_configured(tmp_path: Path) -> None:
    e = Env(tmp_path, admin_token="")
    try:
        assert e.client.get("/stats", headers={"X-Admin-Token": ""}).status_code == 404
    finally:
        e.queue.shutdown()


def test_repo_allowlist_blocks_other_installations(tmp_path: Path) -> None:
    e = Env(tmp_path, allowed_repos=("acme/*",))
    try:
        r = e.post("pull_request", webhook_body("pull_request", e.remote))
        assert r.json() == {"ignored": True} and e.store.job_counts() == {}
    finally:
        e.queue.shutdown()


def test_failure_is_recorded_and_reported_without_claiming_safe(tmp_path: Path) -> None:
    e = Env(tmp_path, git_url_template=str(tmp_path / "nope") + "/{repo}.git")
    try:
        r = e.post("pull_request", webhook_body("pull_request", e.remote))
        e.drain()
        job = e.store.get_job(r.json()["queued"])
        assert job is not None and job.status.value == "failed" and "ScmError" in job.error
        body = e.gh.bot_comment()
        assert "chưa quét xong" in body and "không có nghĩa là mã an toàn" in body
    finally:
        e.queue.shutdown()
