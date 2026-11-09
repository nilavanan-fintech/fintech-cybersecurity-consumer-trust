-- Views that always point at the most recent successful pipeline run (used by Grafana).
CREATE OR REPLACE VIEW latest_run AS
    SELECT run_id FROM pipeline_runs WHERE status = 'success' ORDER BY finished_at DESC LIMIT 1;

CREATE OR REPLACE VIEW v_latest_model_results AS
    SELECT m.* FROM model_results m JOIN latest_run l USING (run_id);

CREATE OR REPLACE VIEW v_latest_txn_daily AS
    SELECT t.* FROM transaction_daily_summary t JOIN latest_run l USING (run_id);

CREATE OR REPLACE VIEW v_latest_security_daily AS
    SELECT s.* FROM security_daily_summary s JOIN latest_run l USING (run_id);

CREATE OR REPLACE VIEW v_latest_trust AS
    SELECT t.* FROM trust_respondent_scores t JOIN latest_run l USING (run_id);
