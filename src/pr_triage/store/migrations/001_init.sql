CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    repo_alias TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    head_sha TEXT NOT NULL,
    base_sha TEXT NOT NULL,
    mode TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    data TEXT NOT NULL
);
CREATE INDEX idx_runs_pr ON runs (repo_alias, pr_number);

CREATE TABLE findings (
    finding_id TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL,
    cwe TEXT,
    data TEXT NOT NULL
);

CREATE TABLE occurrences (
    run_id TEXT NOT NULL,
    finding_id TEXT NOT NULL,
    side TEXT NOT NULL,
    is_new INTEGER NOT NULL,
    data TEXT NOT NULL,
    PRIMARY KEY (run_id, finding_id, side)
);

CREATE TABLE bundles (
    bundle_hash TEXT PRIMARY KEY,
    finding_id TEXT NOT NULL,
    variant TEXT NOT NULL,
    data TEXT NOT NULL
);

CREATE TABLE verdicts (
    run_id TEXT NOT NULL,
    verdict_id TEXT NOT NULL,
    finding_id TEXT NOT NULL,
    variant TEXT NOT NULL,
    model_id TEXT NOT NULL,
    label TEXT NOT NULL,
    data TEXT NOT NULL,
    PRIMARY KEY (run_id, verdict_id)
);
CREATE INDEX idx_verdicts_finding ON verdicts (finding_id, variant);

CREATE TABLE displayed (
    run_id TEXT NOT NULL,
    finding_id TEXT NOT NULL,
    state TEXT NOT NULL,
    data TEXT NOT NULL,
    PRIMARY KEY (run_id, finding_id)
);

CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    finding_id TEXT,
    kind TEXT NOT NULL,
    at TEXT NOT NULL,
    data TEXT NOT NULL
);
CREATE INDEX idx_feedback_run ON feedback (run_id);
