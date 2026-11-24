"""SqlStore: SQLite (WAL) cho bảng quan hệ, BlobStore cho văn bản lớn (ADR 0006)."""

from __future__ import annotations

import datetime as dt
import sqlite3
import threading
from dataclasses import replace
from importlib import resources
from pathlib import Path
from typing import Any

from pr_triage.core.models import (
    Adjudication,
    ContextBundle,
    DisplayedAlert,
    FeedbackEvent,
    Finding,
    Job,
    JobStatus,
    Label,
    Occurrence,
    PoolEntry,
    PostedComment,
    PrRun,
    Verdict,
)
from pr_triage.core.serde import from_json, to_json
from pr_triage.store.blob import BlobStore


def _migrations() -> list[tuple[int, str]]:
    root = resources.files("pr_triage.store") / "migrations"
    items = [
        (int(p.name.split("_")[0]), p.read_text("utf-8"))
        for p in root.iterdir()
        if p.name.endswith(".sql")
    ]
    return sorted(items)


class SqlStore:
    def __init__(self, db_path: str | Path, blob_dir: Path | None = None) -> None:
        self._memory = str(db_path) == ":memory:"
        if not self._memory:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._lock = threading.RLock()
        if not self._memory:
            self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._migrate()
        if blob_dir is None:
            if self._memory:
                import tempfile

                blob_dir = Path(tempfile.mkdtemp(prefix="pr-triage-blobs-"))
            else:
                blob_dir = Path(db_path).parent / "blobs"
        self._blobs = BlobStore(blob_dir)

    def _migrate(self) -> None:
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)"
        )
        done = {r[0] for r in self._db.execute("SELECT version FROM schema_migrations")}
        for version, sql in _migrations():
            if version in done:
                continue
            with self._db:
                self._db.executescript(sql)
                self._db.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))

    def close(self) -> None:
        self._db.close()

    def _exec(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        with self._lock, self._db:
            self._db.execute(sql, params)

    def _one[T](self, cls: type[T], sql: str, params: tuple[Any, ...]) -> T | None:
        with self._lock:
            row = self._db.execute(sql, params).fetchone()
        return from_json(cls, row[0]) if row else None

    def _many[T](self, cls: type[T], sql: str, params: tuple[Any, ...]) -> list[T]:
        with self._lock:
            rows = self._db.execute(sql, params).fetchall()
        return [from_json(cls, r[0]) for r in rows]

    def put_blob(self, data: bytes) -> str:
        return self._blobs.put(data)

    def get_blob(self, ref: str) -> bytes:
        return self._blobs.get(ref)

    def save_run(self, run: PrRun) -> None:
        self._exec(
            "INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?,?,?)",
            (
                run.run_id,
                run.repo_alias,
                run.pr_number,
                run.head_sha,
                run.base_sha,
                run.mode.value,
                run.status.value,
                run.started_at,
                to_json(run),
            ),
        )

    def get_run(self, run_id: str) -> PrRun | None:
        return self._one(PrRun, "SELECT data FROM runs WHERE run_id=?", (run_id,))

    def upsert_finding(self, finding: Finding) -> None:
        self._exec(
            "INSERT OR REPLACE INTO findings VALUES (?,?,?,?)",
            (finding.finding_id, finding.fingerprint, finding.cwe, to_json(finding)),
        )

    def get_finding(self, finding_id: str) -> Finding | None:
        return self._one(Finding, "SELECT data FROM findings WHERE finding_id=?", (finding_id,))

    def add_occurrence(self, occurrence: Occurrence) -> None:
        self._exec(
            "INSERT OR REPLACE INTO occurrences VALUES (?,?,?,?,?)",
            (
                occurrence.run_id,
                occurrence.finding_id,
                occurrence.side.value,
                int(occurrence.is_new),
                to_json(occurrence),
            ),
        )

    def list_occurrences(self, run_id: str) -> list[Occurrence]:
        return self._many(
            Occurrence,
            "SELECT data FROM occurrences WHERE run_id=? ORDER BY finding_id, side",
            (run_id,),
        )

    def save_bundle(self, bundle: ContextBundle) -> None:
        self._exec(
            "INSERT OR REPLACE INTO bundles VALUES (?,?,?,?)",
            (bundle.bundle_hash, bundle.finding_id, bundle.variant.value, to_json(bundle)),
        )

    def get_bundle(self, bundle_hash: str) -> ContextBundle | None:
        return self._one(
            ContextBundle, "SELECT data FROM bundles WHERE bundle_hash=?", (bundle_hash,)
        )

    def save_verdict(self, run_id: str, verdict: Verdict) -> None:
        self._exec(
            "INSERT OR REPLACE INTO verdicts VALUES (?,?,?,?,?,?,?)",
            (
                run_id,
                verdict.verdict_id,
                verdict.finding_id,
                verdict.variant.value,
                verdict.model_id,
                verdict.label.value,
                to_json(verdict),
            ),
        )

    def list_verdicts(self, run_id: str) -> list[Verdict]:
        return self._many(
            Verdict,
            "SELECT data FROM verdicts WHERE run_id=? ORDER BY finding_id, variant",
            (run_id,),
        )

    def save_displayed(self, alert: DisplayedAlert) -> None:
        self._exec(
            "INSERT OR REPLACE INTO displayed VALUES (?,?,?,?)",
            (alert.run_id, alert.finding_id, alert.state.value, to_json(alert)),
        )

    def list_displayed(self, run_id: str) -> list[DisplayedAlert]:
        return self._many(
            DisplayedAlert,
            "SELECT data FROM displayed WHERE run_id=? ORDER BY finding_id",
            (run_id,),
        )

    def add_feedback(self, event: FeedbackEvent) -> None:
        self._exec(
            "INSERT INTO feedback (run_id, finding_id, kind, at, data) VALUES (?,?,?,?,?)",
            (event.run_id, event.finding_id, event.kind.value, event.at, to_json(event)),
        )

    def list_feedback(self, run_id: str) -> list[FeedbackEvent]:
        return self._many(
            FeedbackEvent, "SELECT data FROM feedback WHERE run_id=? ORDER BY id", (run_id,)
        )

    def save_comment(self, comment: PostedComment) -> None:
        self._exec(
            "INSERT OR REPLACE INTO comments VALUES (?,?,?,?,?)",
            (
                comment.run_id,
                comment.comment_ref,
                comment.body_hash,
                comment.posted_at,
                to_json(comment),
            ),
        )

    def get_comment(self, run_id: str) -> PostedComment | None:
        return self._one(PostedComment, "SELECT data FROM comments WHERE run_id=?", (run_id,))

    def list_runs(self) -> list[PrRun]:
        return self._many(PrRun, "SELECT data FROM runs ORDER BY started_at, run_id", ())

    def save_pool_entry(self, entry: PoolEntry) -> None:
        self._exec(
            "INSERT OR REPLACE INTO pool VALUES (?,?,?,?,?)",
            (entry.finding_id, entry.split, entry.run_id, entry.repo_alias, to_json(entry)),
        )

    def list_pool(self, split: str | None = None) -> list[PoolEntry]:
        if split is None:
            return self._many(PoolEntry, "SELECT data FROM pool ORDER BY finding_id", ())
        return self._many(
            PoolEntry, "SELECT data FROM pool WHERE split=? ORDER BY finding_id", (split,)
        )

    def save_label(self, label: Label) -> None:
        self._exec(
            "INSERT OR REPLACE INTO labels VALUES (?,?,?,?)",
            (label.finding_id, label.labeler_alias, label.value.value, to_json(label)),
        )

    def list_labels(self, finding_id: str | None = None) -> list[Label]:
        if finding_id is None:
            return self._many(
                Label, "SELECT data FROM labels ORDER BY finding_id, labeler_alias", ()
            )
        return self._many(
            Label,
            "SELECT data FROM labels WHERE finding_id=? ORDER BY labeler_alias",
            (finding_id,),
        )

    def save_adjudication(self, adj: Adjudication) -> None:
        self._exec(
            "INSERT OR REPLACE INTO adjudications VALUES (?,?,?)",
            (adj.finding_id, adj.final_value.value, to_json(adj)),
        )

    def list_adjudications(self) -> list[Adjudication]:
        return self._many(Adjudication, "SELECT data FROM adjudications ORDER BY finding_id", ())

    # --- hàng đợi việc của GitHub App (ADR 0012 D4) ---
    @staticmethod
    def _now() -> str:
        return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def enqueue_job(self, job: Job) -> Job | None:
        """None nếu lần giao đã có, hoặc đã có việc cùng khóa đang chờ, đang chạy hay đã xong."""
        with self._lock:
            try:
                with self._db:
                    cur = self._db.execute(
                        "INSERT INTO jobs (delivery_id, kind, repo, pr_number, key, status, created_at, data)"
                        " VALUES (?,?,?,?,?,?,?,?)",
                        (job.delivery_id, job.kind.value, job.repo, job.pr_number, job.key,
                         JobStatus.QUEUED.value, self._now(), "{}"),
                    )  # fmt: skip
                    job_id = int(cur.lastrowid or 0)
                    saved = replace(
                        job, job_id=job_id, status=JobStatus.QUEUED, created_at=self._now()
                    )
                    self._db.execute(
                        "UPDATE jobs SET data=? WHERE job_id=?", (to_json(saved), job_id)
                    )
                    return saved
            except sqlite3.IntegrityError:
                return None

    def get_job(self, job_id: int) -> Job | None:
        return self._one(Job, "SELECT data FROM jobs WHERE job_id=?", (job_id,))

    def _update_job(self, job_id: int, **changes: object) -> None:
        with self._lock, self._db:
            row = self._db.execute("SELECT data FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row is None:
                return
            job = replace(from_json(Job, row[0]), **changes)  # type: ignore[arg-type]
            self._db.execute(
                "UPDATE jobs SET status=?, data=? WHERE job_id=?",
                (job.status.value, to_json(job), job_id),
            )

    def claim_job(self, job_id: int) -> Job | None:
        with self._lock:
            job = self.get_job(job_id)
            if job is None or job.status is not JobStatus.QUEUED:
                return None
            self._update_job(
                job_id, status=JobStatus.RUNNING, started_at=self._now(), attempts=job.attempts + 1
            )
            return self.get_job(job_id)

    def finish_job(self, job_id: int, status: JobStatus, error: str = "") -> None:
        self._update_job(job_id, status=status, finished_at=self._now(), error=error[:500])

    def requeue_unfinished(self) -> list[Job]:
        """Khi khởi động lại: việc đang chạy dở được xếp lại hàng."""
        with self._lock:
            rows = self._db.execute(
                "SELECT job_id FROM jobs WHERE status IN ('queued','running') ORDER BY job_id"
            ).fetchall()
            out: list[Job] = []
            for (jid,) in rows:
                self._update_job(jid, status=JobStatus.QUEUED)
                job = self.get_job(jid)
                if job:
                    out.append(job)
            return out

    def latest_job(self, kind: str, repo: str, pr_number: int) -> Job | None:
        return self._one(
            Job,
            "SELECT data FROM jobs WHERE kind=? AND repo=? AND pr_number=? ORDER BY job_id DESC LIMIT 1",
            (kind, repo, pr_number),
        )

    def job_counts(self) -> dict[str, int]:
        with self._lock:
            rows = self._db.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status").fetchall()
        return {r[0]: int(r[1]) for r in rows}

    def list_jobs(self, limit: int = 50) -> list[Job]:
        return self._many(Job, "SELECT data FROM jobs ORDER BY job_id DESC LIMIT ?", (limit,))

    def latest_run_with_comment(
        self, repo_alias: str, pr_number: int
    ) -> tuple[PrRun, PostedComment] | None:
        with self._lock:
            row = self._db.execute(
                "SELECT r.data, c.data FROM runs r JOIN comments c ON c.run_id = r.run_id"
                " WHERE r.repo_alias=? AND r.pr_number=? ORDER BY r.started_at DESC, r.run_id DESC LIMIT 1",
                (repo_alias, pr_number),
            ).fetchone()
        return (from_json(PrRun, row[0]), from_json(PostedComment, row[1])) if row else None

    def previous_run(self, repo_alias: str, pr_number: int, exclude_run: str) -> PrRun | None:
        return self._one(
            PrRun,
            "SELECT data FROM runs WHERE repo_alias=? AND pr_number=? AND run_id<>? AND status<>'failed'"
            " ORDER BY started_at DESC, run_id DESC LIMIT 1",
            (repo_alias, pr_number, exclude_run),
        )
