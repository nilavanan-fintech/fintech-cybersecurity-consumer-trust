-- FinTech Cybersecurity & Consumer Trust - research results schema (PostgreSQL 16)
-- Idempotent: safe to run repeatedly (applied by the container init and by src.database.db.init_schema).
-- Contains ONLY synthetic / pseudonymised research data. No direct identifiers are stored.

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id          TEXT PRIMARY KEY,
    started_at      TIMESTAMP NOT NULL,
    finished_at     TIMESTAMP,
    status          TEXT NOT NULL,
    rows_raw        INTEGER,
    rows_clean      INTEGER,
    seed            INTEGER,
    data_hash       TEXT,
    champion_model  TEXT,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS model_results (
    id                  BIGSERIAL PRIMARY KEY,
    run_id              TEXT NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    model               TEXT NOT NULL,
    model_type          TEXT,
    dataset             TEXT,
    threshold           DOUBLE PRECISION,
    accuracy            DOUBLE PRECISION,
    "precision"         DOUBLE PRECISION,
    recall              DOUBLE PRECISION,
    f1                  DOUBLE PRECISION,
    roc_auc             DOUBLE PRECISION,
    pr_auc              DOUBLE PRECISION,
    false_positive_rate DOUBLE PRECISION,
    tn INTEGER, fp INTEGER, fn INTEGER, tp INTEGER,
    created_at          TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS model_metadata (
    id            BIGSERIAL PRIMARY KEY,
    run_id        TEXT NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    model         TEXT NOT NULL,
    artifact_path TEXT,
    params        TEXT,
    n_features    INTEGER,
    threshold     DOUBLE PRECISION,
    train_seconds DOUBLE PRECISION,
    cv_score      DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS data_quality_checks (
    id           BIGSERIAL PRIMARY KEY,
    run_id       TEXT NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    check_name   TEXT NOT NULL,
    passed       BOOLEAN NOT NULL,
    failed_count INTEGER,
    total        INTEGER,
    detail       TEXT
);

CREATE TABLE IF NOT EXISTS transaction_daily_summary (
    id             BIGSERIAL PRIMARY KEY,
    run_id         TEXT NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    day            TIMESTAMP NOT NULL,
    n_transactions INTEGER,
    n_frauds       INTEGER,
    amount_total   DOUBLE PRECISION,
    amount_fraud   DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS security_daily_summary (
    id        BIGSERIAL PRIMARY KEY,
    run_id    TEXT NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    day       TIMESTAMP NOT NULL,
    n_events  INTEGER,
    n_attacks INTEGER,
    n_blocked INTEGER
);

CREATE TABLE IF NOT EXISTS risk_tier_summary (
    id                  BIGSERIAL PRIMARY KEY,
    run_id              TEXT NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    tier                TEXT NOT NULL,
    transactions        DOUBLE PRECISION,
    frauds              DOUBLE PRECISION,
    amount              DOUBLE PRECISION,
    observed_fraud_rate DOUBLE PRECISION,
    action              TEXT
);

CREATE TABLE IF NOT EXISTS trust_respondent_scores (
    id                  BIGSERIAL PRIMARY KEY,
    run_id              TEXT NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    respondent_id       TEXT NOT NULL,           -- salted-hash pseudonym
    perceived_security  DOUBLE PRECISION,
    privacy_assurance   DOUBLE PRECISION,
    transparency        DOUBLE PRECISION,
    reliability         DOUBLE PRECISION,
    behavioural_intent  DOUBLE PRECISION,
    trust_score         DOUBLE PRECISION,
    segment             TEXT
);

CREATE TABLE IF NOT EXISTS survey_responses (
    id                 BIGSERIAL PRIMARY KEY,
    run_id             TEXT NOT NULL REFERENCES pipeline_runs(run_id) ON DELETE CASCADE,
    respondent_id      TEXT NOT NULL,
    q01 SMALLINT, q02 SMALLINT, q03 SMALLINT, q04 SMALLINT, q05 SMALLINT, q06 SMALLINT,
    q07 SMALLINT, q08 SMALLINT, q09 SMALLINT, q10 SMALLINT, q11 SMALLINT, q12 SMALLINT,
    age_band           TEXT,
    education          TEXT,
    usage_frequency    TEXT,
    uses_mfa           SMALLINT,
    experienced_fraud  SMALLINT,
    digital_literacy   SMALLINT
);

CREATE INDEX IF NOT EXISTS idx_model_results_run ON model_results(run_id);
CREATE INDEX IF NOT EXISTS idx_txn_daily_run_day ON transaction_daily_summary(run_id, day);
CREATE INDEX IF NOT EXISTS idx_sec_daily_run_day ON security_daily_summary(run_id, day);
CREATE INDEX IF NOT EXISTS idx_trust_run ON trust_respondent_scores(run_id);
