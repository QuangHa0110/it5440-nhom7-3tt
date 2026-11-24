"""Hàng đợi việc bền trong SQLite, thực thi bằng nhóm luồng (ADR 0012 D4)."""

from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor, wait

from pr_triage.app.handlers import HANDLERS, Services
from pr_triage.core.models import Job, JobStatus

log = logging.getLogger("pr_triage.app")


class JobQueue:
    def __init__(self, services: Services, workers: int = 2) -> None:
        self.sv = services
        self._pool = ThreadPoolExecutor(max_workers=max(workers, 1), thread_name_prefix="triage")
        self._futures: list[Future[None]] = []

    def submit(self, job: Job) -> Job | None:
        """Lưu việc rồi xếp vào nhóm luồng. None nếu trùng (lần giao hoặc khóa đã có)."""
        saved = self.sv.store.enqueue_job(job)
        if saved is not None:
            self._futures.append(self._pool.submit(self._run, saved.job_id))
        return saved

    def resume(self) -> int:
        jobs = self.sv.store.requeue_unfinished()
        for j in jobs:
            self._futures.append(self._pool.submit(self._run, j.job_id))
        return len(jobs)

    def _run(self, job_id: int) -> None:
        store = self.sv.store
        job = store.claim_job(job_id)
        if job is None:
            return
        try:
            status, note = HANDLERS[job.kind](self.sv, job)
            store.finish_job(job_id, status, note)
        except Exception as exc:  # noqa: BLE001 - mọi lỗi của một việc phải được ghi, không làm chết luồng
            log.exception("job %s (%s %s#%s) lỗi", job_id, job.kind.value, job.repo, job.pr_number)
            store.finish_job(job_id, JobStatus.FAILED, f"{type(exc).__name__}: {exc}")

    def wait_idle(self, timeout: float | None = 120) -> None:
        """Đợi mọi việc đã xếp xong (dùng trong test và khi tắt máy chủ)."""
        wait(list(self._futures), timeout=timeout)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=True, cancel_futures=False)
