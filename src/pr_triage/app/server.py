"""Máy chủ FastAPI: nhận webhook, đưa việc vào hàng đợi, endpoint vận hành (ADR 0012)."""

from __future__ import annotations

import hmac
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from pr_triage.app.handlers import Services
from pr_triage.app.queue import JobQueue
from pr_triage.app.webhook import parse_event, verify_signature
from pr_triage.core.models import Job

log = logging.getLogger("pr_triage.app")


def create_app(sv: Services, queue: JobQueue | None = None) -> FastAPI:
    jobs = queue or JobQueue(sv, sv.settings.workers)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        n = jobs.resume()
        if n:
            log.info("xếp lại %d việc dở dang sau khi khởi động", n)
        yield

    app = FastAPI(
        title="PR Triage", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan
    )
    app.state.queue = jobs
    app.state.services = sv
    counters = {"webhooks": 0, "rejected": 0, "ignored": 0, "queued": 0, "duplicates": 0}

    def admin(token: str | None) -> None:
        expected = sv.settings.admin_token
        if not expected or not token or not hmac.compare_digest(expected, token):
            raise HTTPException(status_code=404)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz() -> JSONResponse:
        try:
            sv.store.job_counts()
        except Exception:  # noqa: BLE001
            return JSONResponse({"status": "database lỗi"}, status_code=503)
        return JSONResponse({"status": "ready"})

    @app.post("/webhook")
    async def webhook(
        request: Request,
        x_hub_signature_256: Annotated[str | None, Header()] = None,
        x_github_event: Annotated[str | None, Header()] = None,
        x_github_delivery: Annotated[str | None, Header()] = None,
    ) -> JSONResponse:
        counters["webhooks"] += 1
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > sv.settings.max_body_bytes:
            counters["rejected"] += 1
            raise HTTPException(status_code=413)
        body = await request.body()
        if len(body) > sv.settings.max_body_bytes:
            counters["rejected"] += 1
            raise HTTPException(status_code=413)
        if not verify_signature(sv.settings.webhook_secret, body, x_hub_signature_256):
            counters["rejected"] += 1
            raise HTTPException(status_code=401, detail="chữ ký không hợp lệ")
        if x_github_event == "ping":
            return JSONResponse({"pong": True})
        try:
            payload: dict[str, Any] = json.loads(body)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="thân không phải JSON") from exc
        event = parse_event(x_github_event or "", payload, sv.auth.bot_login())
        if event is None or not sv.settings.repo_allowed(event.repo):
            counters["ignored"] += 1
            return JSONResponse({"ignored": True}, status_code=200)
        if event.draft and event.kind.value == "triage":
            counters["ignored"] += 1
            return JSONResponse({"ignored": "PR nháp"}, status_code=200)
        saved = jobs.submit(
            Job(
                kind=event.kind,
                repo=event.repo,
                pr_number=event.pr_number,
                installation_id=event.installation_id,
                key=event.key,
                delivery_id=x_github_delivery
                or f"nodelivery-{event.repo}-{event.pr_number}-{event.key}",
            )  # fmt: skip
        )
        if saved is None:
            counters["duplicates"] += 1
            return JSONResponse({"duplicate": True}, status_code=200)
        counters["queued"] += 1
        return JSONResponse({"queued": saved.job_id}, status_code=202)

    @app.get("/stats")
    def stats(x_admin_token: Annotated[str | None, Header()] = None) -> dict[str, Any]:
        admin(x_admin_token)
        return {
            "jobs": sv.store.job_counts(),
            "counters": counters,
            "recent": [
                {"id": j.job_id, "kind": j.kind.value, "repo": j.repo, "pr": j.pr_number,
                 "status": j.status.value, "error": j.error}
                for j in sv.store.list_jobs(20)
            ],
        }  # fmt: skip

    @app.get("/metrics")
    def metrics(x_admin_token: Annotated[str | None, Header()] = None) -> PlainTextResponse:
        admin(x_admin_token)
        lines = []
        for status, n in sorted(sv.store.job_counts().items()):
            lines.append(f'pr_triage_jobs{{status="{status}"}} {n}')
        for name, n in sorted(counters.items()):
            lines.append(f"pr_triage_webhooks_{name} {n}")
        return PlainTextResponse("\n".join(lines) + "\n")

    return app


def build_services(settings_env: dict[str, str] | None = None) -> Services:
    """Lắp dịch vụ thật từ biến môi trường (dùng cho `pr-triage serve`)."""
    from pr_triage.app.auth import AppAuth
    from pr_triage.app.fetcher import GitFetcher
    from pr_triage.app.settings import Settings
    from pr_triage.llm.client import OpenAICompatClient
    from pr_triage.llm.config import LlmConfig
    from pr_triage.llm.engine import PlainTriageEngine, TriageEngine
    from pr_triage.store import SqlStore

    st = Settings.from_env(settings_env)
    cfg = LlmConfig.from_env(settings_env)
    client = OpenAICompatClient(cfg)
    llm = TriageEngine(client) if st.engine == "graph" else PlainTriageEngine(client)
    return Services(
        settings=st,
        auth=AppAuth(st.app_id, st.private_key, st.api_url),
        store=SqlStore(st.db),
        fetcher=GitFetcher(st.git_url_template),
        llm=llm,
    )
