"""Documents 07-13."""
import yaml

import facts as F
from pdfkit import Doc

ROOT = F.ROOT
S = F.settings()
SUM = F.summary()
ST = F.run_status()
FIG = ROOT / "report" / "figures"
NOSUM = "No pipeline run summary exists (models/model_metadata/last_run_summary.json), so no experimental numbers are reported. Run the pipeline and rebuild this pack."


def d07():
    d = Doc("07_Machine_Learning_and_Fraud_Detection.pdf", "07 - Machine Learning and Fraud Detection", "Models, training, tuning, anomaly detection, evaluation",
            ["src/fraud_detection/train.py", "src/fraud_detection/risk.py", "src/anomaly_detection/detectors.py", "src/model_evaluation/evaluate.py", "models/model_metadata/last_run_summary.json"])
    d.h1("Algorithms used and why")
    d.table(["Model", "Type", "Simple explanation", "Imbalance handling", "Tuned parameters (search space)"], [
        ["Logistic Regression", "supervised", "Weighted sum of features turned into a probability; easy to explain to auditors", "class_weight=balanced", "C (log-uniform 1e-3..1e2), after StandardScaler"],
        ["Random Forest", "supervised", "Many decision trees vote; handles non-linear patterns", "balanced_subsample", "max_depth 4-15, min_samples_leaf 2-29, max_features sqrt/0.3/0.5"],
        ["XGBoost", "supervised", "Trees added one by one, each correcting earlier mistakes", "scale_pos_weight = legit/fraud ratio", "max_depth 3-7, learning_rate 0.02-0.3, subsample, colsample_bytree, min_child_weight"],
        ["Isolation Forest", "unsupervised", "Random splits isolate odd points quickly; short path = anomaly", "contamination", "none; fitted without labels"],
        ["Local Outlier Factor", "unsupervised", "Compares a point's local density with its neighbours", "contamination", "n_neighbors=35 on a 6000-row sample"]], widths=[2, 1.3, 3.5, 2, 3.2])
    d.h1("Training procedure (src/fraud_detection/train.py)")
    d.bullets(["Chronological split; features are the 40 columns from feature_names().", "For each enabled model, RandomizedSearchCV (stratified k-fold on the training set, score = average precision) picks hyper-parameters and refits.",
               "The decision threshold is chosen on the validation set to maximise F1 (src/model_evaluation/evaluate.py: best_f1_threshold).",
               "The test set is scored once with the saved threshold. The champion is the supervised model with the highest PR-AUC.", "Models are saved with joblib and a JSON metadata file (parameters, CV score, threshold, features, metrics, data hash, seed, library versions)."])
    d.h2("Risk classification")
    d.table(["Probability", "Tier", "Action"], [[f"< {S['risk_tiers']['low']}", "low", "allow"], [f"{S['risk_tiers']['low']} - {S['risk_tiers']['medium']}", "medium", "step-up authentication"],
        [f"{S['risk_tiers']['medium']} - {S['risk_tiers']['high']}", "high", "hold for manual review"], [f">= {S['risk_tiers']['high']}", "critical", "block + alert"]], widths=[2, 2, 4])
    d.h1("A financial example")
    d.p("Suppose 10,000 card payments contain 200 frauds. A model that flags nothing is 98% accurate yet catches 0 frauds (recall 0). A model that flags 300 payments, 150 truly fraudulent, has precision 0.50 and recall 0.75; its 150 wrong flags are legitimate customers whose card was challenged. "
        "The false-positive rate is 150/9,800 = about 1.5%. This illustrative arithmetic is only an example of the metrics; it is not a result of this project.")
    if SUM:
        m = SUM["models"]; R = m["results"]
        d.h1("Actual results from the last run")
        d.p(f"Run {SUM['run_id']}, seed {SUM['seed']}. Test-set metrics at validation-tuned thresholds. All data are synthetic.")
        d.table(["Model", "Type", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "PR-AUC", "FPR"],
                [[n, m["types"][n], f"{r['accuracy']:.4f}", f"{r['precision']:.3f}", f"{r['recall']:.3f}", f"{r['f1']:.3f}", f"{r['roc_auc']:.3f}", f"{r['pr_auc']:.3f}", f"{r['false_positive_rate']:.4f}"] for n, r in R.items()],
                widths=[2.6, 1.5, 1.2, 1.2, 1, 0.9, 1.1, 1.1, 1])
        d.table(["Model", "TP", "FP", "FN", "TN", "Threshold"], [[n, r["tp"], r["fp"], r["fn"], r["tn"], f"{r['threshold']:.3f}"] for n, r in R.items()], widths=[3, 1, 1, 1, 1.4, 1.6])
        d.table(["Model", "CV average precision", "Train+tune seconds", "Best parameters"], [[n, f"{v['cv_score']:.4f}", f"{v['train_seconds']:.1f}", str(v["params"])] for n, v in m["train"].items()], widths=[2.2, 1.8, 1.7, 5])
        lo, hi = m["champion_roc_auc_ci95"]
        d.p(f"Champion: {m['champion']}. Bootstrap 95% CI of its ROC-AUC: [{lo:.3f}, {hi:.3f}]. McNemar vs Logistic Regression: {m['mcnemar_vs_lr']}.")
        d.h2("Risk tiers on the test set")
        d.table(["Tier", "Transactions", "Frauds", "Observed fraud rate", "Action"], [[r["tier"], int(r["transactions"]), int(r["frauds"]), "n/a" if r["observed_fraud_rate"] is None else f"{r['observed_fraud_rate']:.4f}", r["action"]] for r in m["risk_tiers"]], widths=[1.5, 2, 1.5, 2.5, 3])
        d.image(FIG / "roc_pr_curves.png", "ROC and precision-recall curves (generated by the pipeline).")
        d.image(FIG / "confusion_matrices.png", "Confusion matrices at validation-tuned thresholds (generated by the pipeline).")
        sec = SUM["security"]
        d.h2("Security-event anomaly detection")
        d.p(f"Isolation Forest fitted without labels on the first 70% of time: ROC-AUC against known attacks {sec['anomaly_roc_auc']:.3f}; {sec['anomalies_flagged']} events flagged; attack block rate {sec['attack_block_rate']:.3f}.")
    else:
        d.note(NOSUM)
    d.h2("Implemented vs not implemented")
    d.table(["Item", "Status"], [["LR, RF, XGBoost with tuning", "IMPLEMENTED"], ["Isolation Forest, LOF", "IMPLEMENTED"], ["Bootstrap CI, McNemar test", "IMPLEMENTED"], ["Probability calibration step in pipeline", "MISSING"],
        ["SHAP / explainability", "PLANNED"], ["Multi-seed repeated experiments", "PLANNED"], ["Concept-drift handling", "PLANNED"], ["Public ULB benchmark results", "PENDING"]], widths=[6, 2], status_col=1)
    return d


def d08():
    d = Doc("08_Consumer_Trust_Analytics.pdf", "08 - Consumer Trust Analytics", "Survey instrument, scoring, statistics",
            ["survey/questionnaire.md", "survey/survey_data.csv", "src/trust_scoring/scoring.py", "src/model_evaluation/statistics.py", "src/preprocessing/anonymize.py"])
    d.note("The bundled survey_data.csv is SYNTHETIC (latent-factor generator). Its statistics demonstrate the method and must not be reported as findings about real consumers.")
    d.h1("Instrument")
    from src.schema import SURVEY_ITEMS  # type: ignore
    d.table(["Item", "Statement", "Dimension", "Reverse"], [[q, t, dim, "yes" if rev else "no"] for q, (dim, t, rev) in SURVEY_ITEMS.items()], widths=[0.8, 6, 2.2, 0.9])
    d.p("Behaviour and demographic fields: age_band, education, usage_frequency, uses_mfa, experienced_fraud, digital_literacy. No free text.")
    d.h1("How the score is computed")
    d.flow(["Likert answers q01-q12", "Reverse-code q12", "Dimension means rescaled 0-100", "Weighted sum = CTS", "Segment Low/Moderate/High", "Cronbach alpha", "Drivers: Spearman, OLS", "CTI with PSI"],
           "Implemented in src/trust_scoring/scoring.py.", cols=4)
    d.table(["Quantity", "Definition"], [["CTS", "sum of weight x dimension score / sum of weights"], ["PSI", "100 x mean(recall, 1 - min(10 x FPR, 1), attack block rate, validation pass rate)"],
        ["CTI", f"{S['trust']['survey_weight_in_index']} x mean CTS + {1 - S['trust']['survey_weight_in_index']:.1f} x PSI"]], widths=[1.5, 8])
    d.note("CTI and PSI are the project's own proposals. Their weights are design choices; no psychometric validation (factor analysis, test-retest) has been performed.")
    if SUM:
        t = SUM["trust"]
        d.h1("Actual results from the last run (synthetic survey)")
        d.table(["Quantity", "Value"], [["Respondents", t["n_respondents"]], ["Mean CTS", f"{t['mean_trust_score']:.2f}"], ["PSI", f"{t['platform_security_index']:.2f}"], ["CTI", f"{t['consumer_trust_index']:.2f}"],
            ["OLS R-squared (MFA, past fraud, literacy)", f"{t['ols_r2']:.3f}"], ["Smallest k-anonymity group", t["k_anonymity_min_group"]]], widths=[5, 3])
        d.table(["Dimension", "Mean (0-100)"], [[k, f"{v:.1f}"] for k, v in t["dimension_means"].items()], widths=[4, 2])
        d.table(["Segment", "Respondents"], [[k, v] for k, v in t["segments"].items()], widths=[4, 2])
        d.table(["Scale", "Cronbach alpha"], [[k, "n/a" if v is None else f"{v:.3f}"] for k, v in t["cronbach_alpha"].items()], widths=[4, 2])
        d.table(["Driver", "Spearman rho with CTS", "p-value"], [[k, f"{v:.3f}", f"{t['driver_p_values'][k]:.2e}"] for k, v in t["driver_correlations"].items()], widths=[3, 3, 2])
        d.p("The directions (MFA positive, past fraud negative) are built into the synthetic generator, so agreement with them confirms the pipeline recovers the planted structure; it is not discovery about people.")
        d.image(FIG / "consumer_trust_overview.png", "Trust score distribution, dimension means and Spearman correlations (generated by the pipeline).")
        d.image(FIG / "trust_by_age.png", "Trust score by age band (synthetic).", max_h=8 * 28.35)
    else:
        d.note(NOSUM)
    d.h1("Privacy handling (implemented)")
    d.bullets(["Salted-hash pseudonyms (SURVEY_SALT); age banded; no direct identifiers.", "k-anonymity (k=5) check and suppression: src/preprocessing/anonymize.py."])
    d.h2("Gaps")
    d.table(["Item", "Status"], [["Real respondents / consent records", "MISSING"], ["Ethics approval record", "MISSING"], ["Pilot study for wording and alpha", "PLANNED"], ["Factor analysis / index validation", "PLANNED"], ["Sensitivity analysis notebook (05)", "IMPLEMENTED"]], widths=[6, 2], status_col=1)
    return d


def d09():
    d = Doc("09_Docker_Prometheus_and_Grafana.pdf", "09 - Docker, Prometheus and Grafana", "Containers, metrics, dashboards, logs, alerts",
            ["docker-compose.yml", "infrastructure/docker/*", "dashboard/prometheus/*", "dashboard/grafana/**", "infrastructure/loki, promtail", "src/metrics/exporter.py"])
    comp = F.compose()
    d.h1("Docker architecture")
    d.p("A single Compose project (fintech-research) with one bridge network (fintech-net) and six named volumes (pgdata, prometheus_data, loki_data, grafana_data, app_logs, promtail_positions). Host ports bind to 127.0.0.1 only. Every value has a default so 'docker compose up --build' works without a .env file.")
    d.table(["Service", "Role"], [["postgres", "results and metadata; schema applied from database/ at first start"], ["worker", "runs the pipeline, exposes /metrics on 8000, replays held-out data through the champion model"],
        ["jupyter", "JupyterLab; starts only after worker is healthy"], ["prometheus", "scrapes worker, prometheus, cadvisor, loki, grafana; loads alert rules"], ["loki + promtail", "log storage and shipping"],
        ["cadvisor", "container CPU, memory, network, disk"], ["grafana", "provisioned datasources, dashboards, alert rules"]], widths=[2, 8.5])
    d.h2("Verification state")
    d.table(["Check", "State"], [["Compose file parsed", "VERIFIED"], ["Stack started with docker compose up", ST.get("stack", "NOT VERIFIED")], ["Dashboards viewed in a browser", ST.get("dashboards_viewed", "NOT VERIFIED")]], widths=[5, 3], status_col=1)
    d.h1("Prometheus")
    prom = yaml.safe_load(F.read("dashboard/prometheus/prometheus.yml"))
    d.table(["Job", "Targets", "Purpose"], [[j["job_name"], ", ".join(j["static_configs"][0]["targets"]), ""] for j in prom["scrape_configs"]], widths=[2, 3, 1])
    d.p(f"Global scrape interval: {prom['global']['scrape_interval']}. Alertmanager is intentionally not deployed; alerts are visible in the Prometheus and Grafana UIs.")
    d.h2("Metrics exported by the Python worker (parsed from src/metrics/exporter.py)")
    d.table(["Metric", "Type", "Help text", "Labels"], [list(m) for m in F.metrics()], widths=[4, 1.1, 4.2, 2])
    d.p("Two kinds: gauges describe the last pipeline run (values computed from data and models); counters and a histogram describe the live replay (outcomes, risk tiers, inference latency). Nothing is hardcoded: publish_summary() in the exporter reads the run summary produced by the pipeline.")
    d.h2("Alert rules")
    pr = yaml.safe_load(F.read("dashboard/prometheus/alert_rules.yml"))
    d.table(["Group", "Rule", "Expression"], [[g["name"], r.get("alert") or r.get("record"), " ".join(str(r["expr"]).split())[:90]] for g in pr["groups"] for r in g["rules"]], widths=[2, 3, 5.5])
    gr = yaml.safe_load(F.read("dashboard/grafana/alerts/alert-rules.yml"))
    d.table(["Grafana alert", "Severity", "For"], [[r["title"], r["labels"]["severity"], r["for"]] for g in gr["groups"] for r in g["rules"]], widths=[5, 2, 2])
    d.h1("Loki and Promtail")
    d.p("config/logging.yaml writes JSON log lines (ts, level, logger, msg, optional stage/run_id/model) to logs/fintech.log. Promtail tails that file (shared app_logs volume), extracts level and logger as Loki labels, and pushes to Loki. Dashboards filter with stream selectors such as {job=\"fintech\", level=~\"WARNING|ERROR\"}.")
    d.h1("Grafana dashboards")
    dbs = F.dashboards()
    d.table(["Dashboard", "Panels", "Data sources", "Refresh"], [[x["title"], x["n_panels"], ", ".join(x["sources"]), x["refresh"]] for x in dbs], widths=[4, 1, 4, 1])
    d.p("Dashboards are generated by infrastructure/scripts/build_dashboards.py and provisioned from dashboard/grafana/dashboards (datasource UIDs prometheus, loki, postgres). Panels per dashboard:")
    for x in dbs:
        d.h3(f"{x['title']} ({x['file']})")
        d.table(["Panel", "Type", "Source"], [list(p) for p in x["panels"]], widths=[6, 2, 2.5])
        d.p("Metrics queried: " + ", ".join(x["metrics"]) if x["metrics"] else "No Prometheus metrics (SQL/log panels only).")
    shots = [p for p in (ROOT / "review" / "assets").glob("*.png")] + [p for p in (ROOT / "NotebookLM_Research_Pack" / "screenshots").glob("*.png")]
    d.h1("Screenshots")
    if shots:
        for p in shots:
            d.image(p, f"Screenshot: {p.name}")
    else:
        d.note("No Grafana screenshots exist in the project (review/assets is empty). Capture them from the running stack and re-run this pack builder; none are fabricated.")
    d.h1("PostgreSQL design")
    d.table(["Table", "Columns"], [[t, ", ".join(c)] for t, c in F.sql_tables()], widths=[3, 8])
    d.p("Each table (except pipeline_runs) has run_id referencing pipeline_runs. Views v_latest_* (database/migrations/002_latest_run_views.sql) always point at the most recent successful run and feed the SQL panels. The pipeline falls back to SQLite when DATABASE_URL is not set.")
    return d


def d10():
    d = Doc("10_Implementation_and_Code_Explanation.pdf", "10 - Implementation and Code Explanation", "Module-by-module guide (parsed from the source)",
            ["src/**/*.py", "tests/*.py", "analysis/, notebooks/, survey/ notebooks", "infrastructure/scripts/*"])
    d.h1("How to read the code")
    d.p("Start at src/pipeline.py: run_pipeline() calls the stage packages in order. src/worker.py wraps it as a long-running service. Everything configurable lives in config/settings.yaml.")
    d.h1("Modules")
    for m in F.modules():
        d.h3(f"{m['path']} ({m['lines']} lines)")
        d.p(m["doc"] or "(no module docstring)")
        if m["items"]:
            d.table(["Public name", "Purpose (docstring first line)"], [[n, dsc or "(no docstring)"] for n, dsc in m["items"]], widths=[3, 7.5])
    d.h1("Key algorithms in plain language")
    d.table(["Where", "What happens"], [
        ["features.build_features", "Per customer, running totals minus the current row give the average of PAST amounts; ratio of today's amount to that average flags unusual spending."],
        ["train.train_and_select", "Randomly tries n_iter parameter sets, scores each by 3-fold average precision, refits the best, then picks the F1-optimal threshold on validation data."],
        ["evaluate.best_f1_threshold", "Uses the precision-recall curve and takes the threshold with the highest F1."],
        ["detectors.fit_isolation_forest", "Standardise, fit IsolationForest without labels; anomaly score = negative score_samples."],
        ["scoring.score_respondents", "Reverse-code q12, rescale each dimension to 0-100, weighted average, segment by cut-offs."],
        ["exporter.publish_summary", "Clears and refills labelled gauges from the run summary so Grafana always shows the latest run."],
        ["worker.main", "Starts /metrics, runs the pipeline if artefacts are missing (or FORCE_RETRAIN=1), then loops: score a batch of held-out transactions, increment TP/FP/FN/TN, risk-tier and latency metrics."]], widths=[3, 7.5])
    d.h1("Tests")
    rows = [[f, len(t), "; ".join(t)] for f, t in F.tests()]
    d.table(["Test file", "Count", "Test names"], rows, widths=[2.5, 0.8, 8])
    d.table(["Check", "State"], [["pytest result", ST.get("tests", "NOT VERIFIED")]], widths=[3, 6], status_col=1)
    d.h1("Notebooks")
    d.table(["Notebook", "Title", "Code cells", "Cells with output", "Error outputs"], [[n["path"], n["title"][:48], n["code"], n["with_output"], n["errors"]] for n in F.notebooks()], widths=[4, 4, 1, 1.2, 1])
    d.p("A notebook with zero cells containing outputs has been generated but not executed. Notebooks are generated by infrastructure/scripts/build_notebooks.py and executed by execute_notebooks.py.")
    d.h1("Other scripts")
    d.table(["Script", "Purpose"], [["infrastructure/scripts/generate_synthetic_data.py", "generate datasets only"], ["build_dashboards.py", "regenerate Grafana JSON"], ["build_notebooks.py", "regenerate notebook sources"],
        ["execute_notebooks.py", "execute notebooks in place"], ["initialize_database.sh", "apply schema/migrations/seed outside Docker"], ["run_pipeline.sh", "run the pipeline"]], widths=[5, 5.5])
    d.h2("Incomplete or missing items")
    d.table(["Item", "Status"], [["documentation/*.md written", "IMPLEMENTED"], ["Chapter 5 results and Chapter 6 conclusion in report/chapters", "MISSING" if not (ROOT / "report/chapters/chapter_5_results.md").exists() else "IMPLEMENTED"],
        ["survey/survey_results.md", "MISSING" if not (ROOT / "survey/survey_results.md").exists() else "IMPLEMENTED"], ["Grafana screenshots", "MISSING"], ["Automated test for exporter/worker", "MISSING"], ["CI configuration", "MISSING"]], widths=[7, 2], status_col=1)
    return d


def d11():
    d = Doc("11_Monthly_Project_Reviews.pdf", "11 - Monthly Project Reviews", "Chronological progression from Review 1 to Review 4 (read from the .pptx files)",
            ["review/review_1.pptx ... review_4.pptx", "review/README.md", "review/scripts/*.py"])
    revs = F.reviews()
    d.note("The decks were generated by the scripts in review/scripts. Reviews 3 and 4 read real pipeline output; Reviews 1 and 2 describe design and foundations and claim no results. Dates, student name and guide are placeholders in the decks.")
    names = {1: "Introduction, literature survey, proposed solution", 2: "Methodology, architecture, data, preprocessing, initial implementation",
             3: "Machine learning, anomaly detection, trust scoring, dashboards", 4: "Results, comparison, dashboards, conclusions"}
    d.h1("Progression at a glance")
    d.table(["Review", "Theme", "Slides", "Results shown?"], [[f"Review {i}", names[i], len(revs.get(f'review_{i}', [])) or "deck missing", "no" if i < 3 else "yes (from pipeline output)"] for i in range(1, 5)], widths=[1.3, 5.5, 1.2, 2.5])
    d.flow(["Review 1: idea, gap, plan", "Review 2: method, architecture, data", "Review 3: models, trust, dashboards", "Review 4: results, conclusions"], "Project progression across the four reviews.", cols=4)
    for i in range(1, 5):
        d.pagebreak()
        d.h1(f"Review {i} - {names[i]}")
        slides = revs.get(f"review_{i}")
        if not slides:
            d.note(f"review/review_{i}.pptx was not found; it has not been generated.")
            continue
        for k, (title, body) in enumerate(slides, 1):
            d.h3(f"Slide {k}: {title}")
            if body:
                d.bullets([b[:600] for b in body[:30]])
    d.h1("What changed between reviews")
    d.table(["From -> to", "Added"], [["1 -> 2", "Concrete architecture, stack, datasets, preprocessing, implemented foundations and tests"], ["2 -> 3", "Model training, anomaly detection, trust scoring, dashboards and preliminary results"],
        ["3 -> 4", "Final comparison, statistics, risk tiers, security/trust results, conclusions, limitations, future work"]], widths=[2, 8.5])
    return d


def d12():
    d = Doc("12_Experimental_Results_and_Conclusion.pdf", "12 - Experimental Results and Conclusion", "Only numbers produced by the pipeline",
            ["models/model_metadata/last_run_summary.json", "models/evaluation/*", "report/tables/*", "report/figures/*"])
    if not SUM:
        d.note(NOSUM)
    else:
        m = SUM["models"]; R = m["results"]; ch = m["champion"]
        d.h1("Setup")
        d.table(["Item", "Value"], [["Run id", SUM["run_id"]], ["Seed", SUM["seed"]], ["Rows after cleaning", SUM["cleaning"]["rows_out"]], ["Fraud rate", f"{SUM['transactions']['fraud_rate']:.4%}"],
            ["Tuning iterations per model", S["tuning"]["n_iter"]], ["Library versions", str(SUM["versions"])], ["Total pipeline seconds", f"{SUM['run_seconds']:.1f}"]], widths=[4, 6])
        d.h1("Model comparison")
        d.table(["Model", "Precision", "Recall", "F1", "ROC-AUC", "PR-AUC", "FPR"], [[n, f"{r['precision']:.3f}", f"{r['recall']:.3f}", f"{r['f1']:.3f}", f"{r['roc_auc']:.3f}", f"{r['pr_auc']:.3f}", f"{r['false_positive_rate']:.4f}"] for n, r in R.items()], widths=[3, 1.2, 1.2, 1, 1.2, 1.2, 1.2])
        best_sup = max((n for n in R if m["types"][n] == "supervised"), key=lambda n: R[n]["pr_auc"])
        d.p(f"Champion (highest PR-AUC among supervised models): {best_sup}. Fraud cases in the test set: {R[ch]['tp'] + R[ch]['fn']}; with so few positives the metrics have wide uncertainty - see the bootstrap interval {m['champion_roc_auc_ci95']}.")
        d.image(FIG / "model_comparison.png", "")  # absent unless created
        d.image(FIG / "roc_pr_curves.png", "ROC and precision-recall curves.")
        d.image(FIG / "transaction_overview.png", "Transaction overview: fraud by hour, amount distribution, fraud by category.")
        d.image(FIG / "security_overview.png", "Security events overview.")
        d.h1("Interpretation guardrails")
        d.bullets(["Data are synthetic; fraud patterns were designed by the authors, so high scores show the method works on that design, not that real fraud is this easy.",
                   "Results come from a single seed and a small tuning budget; they are not averaged over repeats.", "The survey is synthetic; trust numbers are demonstration values.",
                   "No claim is made about real-world deployment performance."])
    d.h1("Conclusions the project can support")
    d.bullets(["A reproducible, containerised pipeline links fraud and anomaly detection with a consumer trust measure and monitors the experiment.", "Models are compared with imbalance-aware metrics and false-positive cost rather than accuracy alone.",
               "Unsupervised detectors are evaluated separately from supervised models.", "Dashboards, logs and database views are driven by computed data."])
    d.h1("Limitations (from the project documents)")
    d.bullets(["Synthetic data encode assumptions; no concept drift.", "Synthetic survey; no ethics approval recorded.", "Trust Index is a proposal without psychometric validation.", "Replay stream is not production traffic.", "Alertmanager not deployed."])
    d.h1("Future work (planned, not implemented)")
    d.bullets(["Run on the public ULB dataset and repeat across seeds.", "Real ethics-approved survey; factor analysis.", "Calibration, cost-sensitive thresholds, SHAP explanations.", "Drift monitoring, scheduled retraining, Alertmanager.", "Use unsupervised scores as features for supervised models."])
    return d


def d13():
    d = Doc("13_Final_Year_Viva_Preparation.pdf", "13 - Final Year Viva Preparation", "Questions grounded in this project",
            ["all project files", "11_Monthly_Project_Reviews", "12_Experimental_Results_and_Conclusion"])
    d.note("Answers refer to what the repository actually contains. Where you are unsure whether something has been run, check the verification table in document 01 first.")
    def champ():
        return f"In the last run the champion was {SUM['models']['champion']}" if SUM else "Run the pipeline to know the champion"
    qa = [
        ("Why did you use synthetic data?", "Real fraud and customer data are sensitive and not available for a student project; synthetic data lets experiments run in an isolated environment with known labels and a fixed seed. The limitation is that results validate the method, not real prevalence."),
        ("Why not use accuracy?", "Fraud is about 2% of transactions, so predicting 'legitimate' every time scores ~98% accuracy while catching nothing. We use precision, recall, F1, PR-AUC and false-positive rate."),
        ("Why PR-AUC to pick the champion?", "It focuses on the rare positive class, whereas ROC-AUC can look optimistic when negatives dominate (Saito and Rehmsmeier is cited in references.bib)."),
        ("Why a chronological split?", "Shuffled splits let the model learn from the future. Fraud evolves over time, so we train on the earliest 70%, tune the threshold on the next 15% and test once on the latest 15%."),
        ("How do you prevent leakage?", "Customer-history features use cumulative sums minus the current row; a unit test changes the last transaction and checks earlier features do not change. fraud_pattern is never a feature."),
        ("Why class weights instead of SMOTE?", "Resampling distorts predicted probabilities, which we use for risk tiers; class weights keep the data intact (Dal Pozzolo et al. discuss this in references.bib)."),
        ("How is the threshold chosen?", "Maximum F1 on the validation set, then fixed for the test set, so the test set is not used for tuning."),
        ("Explain Isolation Forest.", "It builds random trees; anomalies are isolated in fewer splits. It needs no labels, which suits delayed-label situations; labels are used only afterwards to evaluate."),
        ("What is the false-positive rate and why does it matter for trust?", "FP/(FP+TN): legitimate customers wrongly challenged. Each wrong block is friction that can reduce trust; the Platform Security Index penalises it."),
        ("What is the Consumer Trust Index?", "A proposed composite: 0.6 x mean survey trust score + 0.4 x Platform Security Index. Weights are design choices; the project reports sensitivity but has not validated the index psychometrically."),
        ("Is your survey real?", "No. The bundled survey_data.csv is synthetic. The questionnaire and ethics checklist are real design artefacts; real collection needs ethics approval, which is not recorded."),
        ("What does Cronbach's alpha tell you?", "Internal consistency of the items (Cronbach 1951); about 0.7 or higher is conventionally acceptable. On synthetic data it reflects the generator, not real respondents."),
        ("How does Grafana show real data?", "The worker computes metrics from the pipeline and from a replay of held-out transactions through the trained model, and Prometheus scrapes them. Panels are PromQL, LogQL or SQL queries, not typed values."),
        ("What is the live replay?", "After training, the worker feeds held-out test transactions in batches through the champion model and increments TP/FP/FN/TN counters. It is a replay, not production traffic."),
        ("Why Prometheus, Loki and PostgreSQL together?", "Prometheus for numeric time series, Loki for logs, PostgreSQL for structured results and run history; Grafana can query all three."),
        ("What happens on docker compose up?", "postgres starts and applies the schema; the worker builds data, trains, evaluates, writes artefacts and publishes metrics, becoming healthy when fintech_pipeline_ready is 1; then jupyter starts. Prometheus, Loki, Promtail, cAdvisor and Grafana start with health checks."),
        ("How is reproducibility ensured?", "Seeds in settings.yaml, data hash and library versions saved in model metadata, containers, tests. With end_date 'auto' the dates move with the run date but values are the same."),
        ("Which model won?", f"{champ()}. State the numbers from document 12 and mention the small number of test frauds and single seed."),
        ("What are the main limitations?", "Synthetic data and survey, single seed, small tuning budget, no drift, unvalidated index, no ethics approval recorded, replay not production."),
        ("What would you do next?", "Run the ULB dataset, repeat over seeds, collect real consented survey data, add calibration and SHAP, drift monitoring and Alertmanager."),
        ("How did the project progress over four reviews?", "Review 1: problem, objectives, literature, gap, plan. Review 2: methodology, architecture, data, preprocessing and foundations. Review 3: models, trust scoring, dashboards and preliminary results. Review 4: final comparison, dashboards, conclusions."),
    ]
    d.h1("Questions and model answers")
    for i, (q, a) in enumerate(qa, 1):
        d.h3(f"Q{i}. {q}")
        d.p(a)
    d.h1("Honesty checklist before the viva")
    d.bullets(["Say clearly that data and survey are synthetic.", "Do not quote results without the seed, test-set size and uncertainty.", "Do not claim ethics approval or real respondents.", "Be ready to show: tests passing, pipeline summary, one Grafana dashboard live.",
               "Know what is planned versus implemented (documents 01, 07, 08, 10)."])
    d.h1("Demo plan")
    d.bullets(["docker compose up --build; wait for worker healthy.", "Grafana Overview -> Pipeline Monitoring -> Fraud -> Model Performance -> Trust -> Infrastructure.", "Jupyter notebook 07 for evaluation; open a Loki log line.", "Fallback if the stack is slow: show notebooks and report/figures."])
    return d
