"""SqlStore: SQLite (WAL) cho bảng quan hệ, BlobStore cho văn bản lớn (ADR 0006)."""

from __future__ import annotations

import sqlite3
import threading
from importlib import resources
from pathlib import Path
from typing import Any

from pr_triage.core.models import (
    ContextBundle,
    DisplayedAlert,
    FeedbackEvent,
    Finding,
    Occurrence,
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
