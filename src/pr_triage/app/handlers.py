"""Xử lý từng loại việc: triage một PR, thu phản hồi, chốt khi PR đóng (ADR 0012)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from pr_triage.app.auth import AppAuth
from pr_triage.app.fetcher import GitFetcher
from pr_triage.app.fixpass import mark_fixed
from pr_triage.app.settings import Settings
from pr_triage.bot import (
    MARKER,
    FeedbackCollector,
    Publisher,
    compute_cc,
    render,
    resolve_states,
)
from pr_triage.bot.github import GitHubApi, GitHubScm, PrInfo
from pr_triage.core.alias import Aliaser
from pr_triage.core.models import (
    Job,
    JobKind,
    JobStatus,
    PrRef,
    PrRun,
    RunMode,
    RunStatus,
    TriageResult,
    Variant,
)
from pr_triage.core.ports import LlmPort
from pr_triage.pipeline import codeowners
from pr_triage.pipeline.build import BuildOptions, build_pipeline
from pr_triage.pipeline.repoconfig import ConfigError, RepoConfig, parse_config
from pr_triage.store import SqlStore

log = logging.getLogger("pr_triage.app")
CODEOWNERS_PATHS = (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS")
CONFIG_PATH = ".pr-triage.yml"


@dataclass
class Services:
    settings: Settings
    auth: AppAuth
    store: SqlStore
    fetcher: GitFetcher
    llm: LlmPort
    transport: httpx.BaseTransport | None = None

    def api(self, token: str) -> GitHubApi:
        return GitHubApi(token, self.settings.api_url, self.transport, backoff_s=1.0)

    def scm(self, token: str) -> GitHubScm:
        return GitHubScm(token, self.settings.api_url, self.transport, backoff_s=1.0)


def _note(scm: GitHubScm, pr: PrRef, title: str, text: str) -> None:
    """Đăng một thông báo ngắn thay cho kết quả (cấu hình sai, PR quá lớn, quét lỗi)."""
    body = "\n".join([MARKER, f"## Kiểm tra bảo mật: {title}", "", text])
    scm.upsert_comment(pr, MARKER, body)


def _load_config(api: GitHubApi, repo: str, base_sha: str) -> RepoConfig:
    return parse_config(api.get_file(repo, CONFIG_PATH, base_sha))


def _codeowner_rules(api: GitHubApi, repo: str, base_sha: str) -> list[codeowners.Rule]:
    for path in CODEOWNERS_PATHS:
        text = api.get_file(repo, path, base_sha)
        if text is not None:
            return codeowners.parse(text)
    return []


def _pr_ref(info: PrInfo) -> PrRef:
    return PrRef(info.repo, info.number, info.head_sha, info.base_sha, info.author)


def handle_triage(sv: Services, job: Job) -> tuple[JobStatus, str]:
    token = sv.auth.installation_token(job.installation_id)
    api, scm = sv.api(token), sv.scm(token)
    info = api.get_pr(job.repo, job.pr_number)
    if info.head_sha != job.key:
        return JobStatus.SKIPPED, "PR đã có commit mới hơn"
    pr = _pr_ref(info)
    try:
        cfg = _load_config(api, job.repo, info.base_sha)
    except ConfigError as exc:
        _note(scm, pr, "cấu hình `.pr-triage.yml` sai", "\n".join(f"- {p}" for p in exc.problems))
        return JobStatus.FAILED, f"cấu hình sai: {exc}"
    if not cfg.enabled:
        return JobStatus.SKIPPED, "bot bị tắt trong cấu hình"
    if info.draft:
        return JobStatus.SKIPPED, "PR nháp"
    if info.changed_files > cfg.max_changed_files:
        _note(
            scm, pr, "bỏ qua vì PR quá lớn",
            f"PR có {info.changed_files} tệp, vượt giới hạn {cfg.max_changed_files}. "
            "Việc không quét không có nghĩa là mã an toàn.",
        )  # fmt: skip
        return JobStatus.SKIPPED, "PR quá lớn"
    mode = RunMode.COMMENT if cfg.mode == "comment" else RunMode.SHADOW
    base = api.merge_base(job.repo, info.base_sha, info.head_sha)
    prev = sv.store.previous_run(job.repo, job.pr_number, "")
    opts = BuildOptions(
        rules=sv.settings.rules, catalog=sv.settings.catalog, db=sv.settings.db,
        repo_alias=job.repo, mode=mode, display=Variant(cfg.display), engine=sv.settings.engine,
        workers=sv.settings.pipeline_workers, secrets=cfg.secrets, min_severity=cfg.min_severity,
        max_findings=cfg.max_findings, path_include=cfg.paths.include,
        path_exclude=cfg.paths.exclude,
    )  # fmt: skip
    optional = [prev.head_sha] if prev and prev.head_sha not in (info.head_sha, base) else []
    try:
        pipeline, _ = build_pipeline(opts, llm=sv.llm, store=sv.store)
        with sv.fetcher.checkout(
            job.repo, token, [base, info.head_sha], job.pr_number, optional
        ) as repo:
            result = pipeline.run(repo, base, info.head_sha, job.pr_number, exact_base=True)
            if prev is not None and result.run.status is not RunStatus.FAILED:
                try:
                    mark_fixed(sv.store, repo, prev, result.run)
                except Exception:  # noqa: BLE001 - phần phụ, không làm hỏng lượt chạy
                    log.exception("mark_fixed lỗi (job %s)", job.job_id)
    except Exception as exc:
        failed = TriageResult(
            PrRun(
                "failed", job.repo, job.pr_number, info.head_sha, base, mode, RunStatus.FAILED, ""
            ),
            errors=(type(exc).__name__,),
        )
        if mode is RunMode.COMMENT:
            scm.upsert_comment(pr, MARKER, render(failed))
        raise
    latest = sv.store.latest_job(JobKind.TRIAGE.value, job.repo, job.pr_number)
    if latest is not None and latest.job_id > job.job_id:
        return JobStatus.SKIPPED, "có lượt chạy mới hơn, không đăng kết quả cũ"
    rules = (
        _codeowner_rules(api, job.repo, info.base_sha) if "codeowners" in cfg.mentions.mode else []
    )
    cc = compute_cc(
        result, cfg.mentions.mode, cfg.mentions.min_severity, info.author, cfg.mentions.users,
        owners_of=lambda files: codeowners.owners_for(files, rules), exclude=[sv.auth.bot_login()],
    )  # fmt: skip
    Publisher(scm, sv.store).publish(result, pr, post=True, cc=cc, check=cfg.check_run)
    return JobStatus.DONE, ""


def _collect(sv: Services, job: Job, closed: bool) -> tuple[JobStatus, str]:
    token = sv.auth.installation_token(job.installation_id)
    api, scm = sv.api(token), sv.scm(token)
    found = sv.store.latest_run_with_comment(job.repo, job.pr_number)
    if found is None:
        return JobStatus.SKIPPED, "chưa có comment của bot trên PR này"
    run, comment = found
    info = api.get_pr(job.repo, job.pr_number)
    pr = _pr_ref(info)
    try:
        cfg = _load_config(api, job.repo, info.base_sha)
    except ConfigError:
        cfg = RepoConfig()
    result = TriageResult(run, displayed=tuple(sv.store.list_displayed(run.run_id)))
    FeedbackCollector(scm, sv.store, Aliaser(sv.settings.alias_salt)).collect(
        result, pr, comment.comment_ref
    )
    state = scm.pr_state(pr)
    for alert in resolve_states(
        result.displayed, sv.store.list_feedback(run.run_id),
        closed=closed or state != "open", trusted_roles=cfg.trusted_roles,
    ):  # fmt: skip
        sv.store.save_displayed(alert)
    return JobStatus.DONE, ""


def handle_feedback(sv: Services, job: Job) -> tuple[JobStatus, str]:
    return _collect(sv, job, closed=False)


def handle_close(sv: Services, job: Job) -> tuple[JobStatus, str]:
    return _collect(sv, job, closed=True)


HANDLERS = {
    JobKind.TRIAGE: handle_triage,
    JobKind.FEEDBACK: handle_feedback,
    JobKind.CLOSE: handle_close,
}

__all__ = ["HANDLERS", "Services"]
