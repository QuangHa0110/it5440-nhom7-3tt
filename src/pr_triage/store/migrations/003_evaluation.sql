CREATE TABLE pool (
    finding_id TEXT PRIMARY KEY,
    split TEXT NOT NULL,
    run_id TEXT NOT NULL,
    repo_alias TEXT NOT NULL,
    data TEXT NOT NULL
);

CREATE TABLE labels (
    finding_id TEXT NOT NULL,
    labeler_alias TEXT NOT NULL,
    value TEXT NOT NULL,
    data TEXT NOT NULL,
    PRIMARY KEY (finding_id, labeler_alias)
);

CREATE TABLE adjudications (
    finding_id TEXT PRIMARY KEY,
    final_value TEXT NOT NULL,
    data TEXT NOT NULL
);
