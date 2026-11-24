CREATE TABLE jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_id TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL,
    repo TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    key TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    data TEXT NOT NULL
);
CREATE INDEX idx_jobs_status ON jobs (status);
CREATE INDEX idx_jobs_pr ON jobs (repo, pr_number, kind, job_id);
CREATE UNIQUE INDEX idx_jobs_key ON jobs (kind, repo, pr_number, key)
    WHERE status IN ('queued', 'running', 'done');
