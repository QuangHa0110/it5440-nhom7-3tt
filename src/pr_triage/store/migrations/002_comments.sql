CREATE TABLE comments (
    run_id TEXT PRIMARY KEY,
    comment_ref TEXT NOT NULL,
    body_hash TEXT NOT NULL,
    posted_at TEXT NOT NULL,
    data TEXT NOT NULL
);
