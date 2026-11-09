"""Documents 01-06."""
import facts as F
from pdfkit import Doc

S = F.settings()
ST = F.run_status()


def verified(key, ok_text, default="NOT VERIFIED"):
    v = ST.get(key)
    return v if v else default


def d01():
    d = Doc("01_Project_Overview.pdf", "01 - Project Overview", "FinTech Cybersecurity and Consumer Trust",
            ["README.md", "documentation/project_overview.md", "config/settings.yaml", "docker-compose.yml"])
    d.h1("What the project is")
    d.p("This is a final-year research and development project. It builds a Python-based research platform (no web front end) that studies how "
        "cybersecurity capability in FinTech - fraud detection, anomaly detection, threat monitoring - relates to consumer trust, and that exposes the live state of "
        "the experiment through Prometheus, Grafana and Loki.")
    d.h2("One-paragraph summary")
    d.p("Synthetic financial transactions, synthetic security events and a synthetic consumer survey are generated with a fixed random seed. A pipeline validates and "
        "cleans the data, engineers features, trains and tunes three supervised models (Logistic Regression, Random Forest, XGBoost) and two unsupervised detectors "
        "(Isolation Forest, Local Outlier Factor), evaluates them on a chronological test set, classifies risk into tiers, scores consumer trust from Likert answers, "
        "stores results in PostgreSQL and publishes metrics. Docker Compose starts everything with one command.")
    d.h2("The big idea in simple words")
    d.p("A bank app can be technically very secure but customers may still not trust it; or customers may trust it while it is weakly protected. The project measures both sides - "
        "how well the system catches fraud (measured) and how safe people feel (surveyed) - and watches the whole experiment on dashboards.")
    d.h2("Main components")
    d.table(["Component", "Where", "Status"], [
        ["Research pipeline (collect to report)", "src/pipeline.py + src/* packages", "IMPLEMENTED"],
        ["Fraud + anomaly models", "src/fraud_detection, src/anomaly_detection", "IMPLEMENTED"],
        ["Consumer trust scoring + statistics", "src/trust_scoring, src/model_evaluation", "IMPLEMENTED"],
        ["PostgreSQL schema and persistence", "database/, src/database/db.py", "IMPLEMENTED"],
        ["Prometheus exporter and live replay worker", "src/metrics/exporter.py, src/worker.py", "IMPLEMENTED"],
        ["Grafana dashboards, datasources, alerts", "dashboard/grafana, dashboard/prometheus", "IMPLEMENTED"],
        ["Docker Compose stack (8 services)", "docker-compose.yml, infrastructure/", "IMPLEMENTED"],
        ["16 Jupyter notebooks", "analysis/, notebooks/, survey/", "IMPLEMENTED"],
        ["Real survey data, ethics approval", "survey/survey_data.csv is synthetic", "MISSING"],
        ["Public-dataset benchmark results", "code path exists; needs creditcard.csv in data/external", "PENDING"]], widths=[4, 4, 1.6], status_col=2)
    d.h2("Verification state when this pack was generated")
    d.table(["Check", "State"], [
        ["Unit tests (pytest)", verified("tests", "")], ["Full pipeline run produced results", "VERIFIED" if F.summary() else "NOT VERIFIED"],
        ["Notebooks executed with stored outputs", verified("notebooks", "")], ["Docker Compose stack started and dashboards viewed", verified("stack", "")],
        ["Four review decks generated", "VERIFIED" if len(F.reviews()) == 4 else "NOT VERIFIED"]], widths=[5, 5], status_col=1)
    d.note("Where a state says NOT VERIFIED the code exists but was not executed end-to-end in the environment used to prepare this pack. Details are in the validation report.")
    d.h2("Repository map")
    d.table(["Folder", "Purpose"], [
        ["analysis/", "7 focused analysis notebooks"], ["notebooks/", "01-08 research sequence"], ["survey/", "questionnaire, synthetic data, analysis notebook"],
        ["src/", "pipeline code by stage"], ["models/", "serialized models, evaluation, metadata (created by pipeline)"], ["database/", "schema, migrations, seed data"],
        ["dashboard/", "Grafana + Prometheus configuration"], ["infrastructure/", "Dockerfiles, Loki/Promtail config, helper scripts"],
        ["config/", "settings.yaml, logging.yaml"], ["documentation/", "9 documentation files"], ["report/", "6 chapter drafts, references.bib, figures, tables"],
        ["review/", "four monthly decks + generation scripts"], ["tests/", "pytest suite"]], widths=[3, 7])
    return d


def d02():
    d = Doc("02_Problem_Statement_and_Objectives.pdf", "02 - Problem Statement and Objectives", "From the project's own documentation",
            ["documentation/project_overview.md", "documentation/research_questions.md", "report/chapters/chapter_1_introduction.md"])
    d.h1("Problem statement")
    d.bullets(["Fraud-detection research often optimises predictive metrics on a single dataset and reports accuracy, which is misleading when fraud is ~2% of transactions.",
               "Consumer-trust research relies on surveys that are disconnected from measured security performance.",
               "Detection errors have a consumer cost: a false positive blocks or challenges a legitimate customer.",
               "Research pipelines are rarely observable: results are not monitored or easily reproduced."])
    d.h1("Aim")
    d.p("Build and evaluate a reproducible platform that links fraud and threat detection with consumer trust and monitors the experiment.")
    d.h1("Objectives")
    d.table(["ID", "Objective", "Where addressed in the code"], [
        ["O1", "Reproducible pipeline for transaction and security-event data", "src/pipeline.py, src/data_collection, src/preprocessing"],
        ["O2", "Compare supervised and unsupervised detectors with imbalance-aware metrics", "src/fraud_detection/train.py, src/anomaly_detection/detectors.py, src/model_evaluation/evaluate.py"],
        ["O3", "Quantify the cost of detection errors", "false_positive_rate metric, risk tiers (src/fraud_detection/risk.py), notebook 07"],
        ["O4", "Measure consumer trust with a privacy-conscious survey", "survey/questionnaire.md, src/trust_scoring/scoring.py, src/preprocessing/anonymize.py"],
        ["O5", "Propose and stress-test a composite Consumer Trust Index", "scoring.consumer_trust_index, notebook 05 sensitivity analysis"],
        ["O6", "Make the pipeline observable in Grafana with real data", "src/metrics/exporter.py, dashboard/"]], widths=[0.8, 4.5, 5])
    d.h1("Research questions and hypotheses")
    d.table(["ID", "Research question"], [
        ["RQ1", "Which supervised model gives the best fraud trade-off (PR-AUC, recall, false-positive rate)?"],
        ["RQ2", "How far can label-free detectors (Isolation Forest, LOF) get compared with supervised learning?"],
        ["RQ3", "What do detection errors cost the consumer at different thresholds?"],
        ["RQ4", "Which signals characterise each fraud pattern and which patterns evade detection?"],
        ["RQ5", "How do consumers perceive FinTech cybersecurity and which factors relate to trust?"],
        ["RQ6", "Can perceived trust and measured security be combined into a stable index?"],
        ["RQ7", "Can pipeline health and model quality be monitored with open-source observability tools?"]], widths=[1, 9])
    d.p("Hypotheses H1-H7 (amount differs for fraud; channel and authentication associated with fraud; trust differs by age; past fraud experience lowers trust; boosted trees beat Logistic Regression on PR-AUC; MFA users report higher perceived security) are listed in documentation/research_questions.md.")
    d.note("Status: hypotheses are tested only on synthetic data in this repository. No hypothesis has been tested on real consumers.")
    d.h1("Scope and ethics")
    d.bullets(["Security experiments use synthetic data inside an isolated Docker network, or an optional licensed public dataset the user downloads.",
               "Survey design: voluntary, no free text, banded demographics, salted-hash pseudonyms, k-anonymity (k=5).",
               "Ethics approval is listed as a required checkbox in survey/questionnaire.md and is NOT recorded as obtained."])
    return d


def d03():
    d = Doc("03_Literature_Review_and_Research_Gap.pdf", "03 - Literature Review and Research Gap", "Only references present in report/references.bib",
            ["report/references.bib", "report/chapters/chapter_2_literature_review.md", "review/review_1.pptx"])
    bib = F.read("report/references.bib")
    import re
    entries = re.findall(r"@\w+\{(\w+),(.*?)\n\}", bib, re.S)
    d.note("These are the works cited in the project's own references.bib. This pack adds no other citations. The bib file itself says to verify each entry against the publisher record before submission; that verification has not been done by this pack.")
    d.h1("Themes and how each informs the project")
    d.table(["Theme", "Cited works (bib keys)", "How the project uses it"], [
        ["ML fraud detection", "ngai2011application, bhattacharyya2011data, chen2016xgboost, breiman2001random", "Logistic Regression, Random Forest, XGBoost as supervised models"],
        ["Feature engineering", "bahnsen2016feature", "History-based aggregates vs the customer's prior mean"],
        ["Imbalance and evaluation", "davis2006relationship, saito2015precision, dalpozzolo2015calibrating", "PR-AUC emphasis; class weights instead of resampling"],
        ["Anomaly detection", "liu2008isolation, breunig2000lof, chandola2009anomaly", "Isolation Forest and LOF"],
        ["Hyper-parameter search", "bergstra2012random", "RandomizedSearchCV"],
        ["Trust in e-commerce", "mcknight2002developing, gefen2003trust, pavlou2003consumer, davis1989perceived", "Multi-dimensional trust; five survey dimensions"],
        ["Measurement and privacy", "cronbach1951coefficient, likert1932technique, sweeney2002kanonymity", "Cronbach's alpha; Likert items; k-anonymity"],
        ["Tooling", "pedregosa2011scikit", "scikit-learn"]], widths=[2.3, 4.5, 4])
    d.h1("Bibliography as recorded in references.bib")
    rows = []
    for key, body in entries:
        g = lambda f: (re.search(f + r"\s*=\s*\{(.*?)\}\s*,?\s*(?:\n|$)", body, re.S) or [None, ""])[1].replace("\n", " ").strip()
        rows.append([key, g("author")[:70], g("title")[:90], g("year")])
    d.table(["Key", "Authors", "Title", "Year"], rows, widths=[2.2, 3.2, 5, 0.8])
    d.h1("Research gap (as stated in the project)")
    d.bullets(["Strong fraud models are usually evaluated in isolation.", "Trust surveys are run without security telemetry.",
               "Monitoring is treated as an operations topic, not as a research instrument.",
               "Missing: a joint view of measured security and perceived trust, a transparent and sensitivity-tested composite index, and a reproducible, observable research platform."])
    d.h2("Position of the project against the gap")
    d.table(["Gap element", "Project response", "Status"], [
        ["Joint view of security and trust", "Platform Security Index + Consumer Trust Score -> Consumer Trust Index", "IMPLEMENTED"],
        ["Sensitivity-tested index", "notebook 05: survey weight sweep and random dimension weights", "IMPLEMENTED"],
        ["Validated index", "No psychometric validation (e.g. factor analysis) done", "MISSING"],
        ["Reproducible, observable platform", "Docker Compose + Prometheus/Grafana/Loki", "IMPLEMENTED"],
        ["Review of literature beyond the bib list", "chapter_2_literature_review.md is a short draft (~7 sections)", "PARTIAL"]], widths=[3, 5.5, 1.6], status_col=2)
    d.note("Missing documentation: the literature review draft does not yet compare studies in depth (datasets, reported metrics) and contains no table of reviewed papers' results. Do not invent such comparisons.")
    return d


def d04():
    d = Doc("04_Research_Methodology.pdf", "04 - Research Methodology", "How the experiments are designed",
            ["documentation/methodology.md", "src/pipeline.py", "config/settings.yaml", "report/chapters/chapter_3_methodology.md"])
    d.h1("Research design")
    d.p("Design-science style computer-science experiment plus a quantitative survey component. Everything is seeded and logged; each model's metadata stores a data hash, seed and library versions.")
    d.h1("Pipeline stages (in order)")
    d.flow(["collect", "validate", "clean", "features", "train (tune)", "evaluate", "anomaly", "security", "risk", "trust", "persist", "external benchmark (optional)", "report", "database"],
           "Stages as implemented in src/pipeline.py; each is timed and exported as a Prometheus metric.", cols=4)
    d.h1("Experimental protocol")
    sp, tu = S["split"], S["tuning"]
    d.table(["Item", "Setting in config/settings.yaml", "Why"], [
        ["Seed", str(S["seed"]), "Reproducibility"],
        ["Split", f"chronological train {sp['train']} / validation {sp['validation']} / rest test", "Prevents leakage from the future"],
        ["Tuning", f"RandomizedSearchCV, n_iter={tu['n_iter']}, cv_folds={tu['cv_folds']}, scoring={tu['scoring']}", "Random search is efficient; average precision suits rare positives"],
        ["Imbalance", "class_weight='balanced' (LR), 'balanced_subsample' (RF), scale_pos_weight (XGBoost)", "No resampling, so probabilities stay meaningful for risk tiers"],
        ["Threshold", "F1-optimal on the validation set", "Test set untouched until final evaluation"],
        ["Anomaly contamination", str(S["anomaly"]["contamination"]), "Expected outlier share; threshold taken from validation scores"]], widths=[2.3, 5.5, 3])
    d.h2("Evaluation metrics")
    d.table(["Metric", "Meaning in a fraud context"], [
        ["Accuracy", "Share of correct predictions - misleading: predicting 'legit' always gives ~98% when fraud is ~2%"],
        ["Precision", "Of transactions flagged as fraud, how many really are fraud"], ["Recall", "Of real frauds, how many were caught"],
        ["F1", "Harmonic mean of precision and recall"], ["ROC-AUC", "Ranking quality over all thresholds; can look optimistic under imbalance"],
        ["PR-AUC (average precision)", "Ranking quality focused on the rare positive class; used to choose the champion"],
        ["False-positive rate", "Share of legitimate transactions wrongly flagged = customer friction"],
        ["Confusion matrix", "TP, FP, FN, TN counts"], ["Bootstrap 95% CI", "Uncertainty of champion ROC-AUC (200 resamples)"], ["McNemar test", "Are two models' errors different on the same test cases"]], widths=[2.8, 7.5])
    d.h1("Consumer trust methodology")
    d.bullets(["12 Likert items (1-5) in five dimensions; q12 is reverse-coded (6 - x).", "Dimension score = (mean - 1) / 4 x 100; Consumer Trust Score (CTS) = weighted mean of dimensions.",
               f"Weights from settings.yaml: {S['trust']['weights']}", f"Segments: Low < {S['trust']['segments']['low']}, High >= {S['trust']['segments']['high']}, otherwise Moderate.",
               "Reliability: Cronbach's alpha. Drivers: Spearman correlation, OLS on standardised predictors, Kruskal-Wallis, Mann-Whitney.",
               "Platform Security Index (PSI) = 100 x mean(recall, 1 - min(10 x FPR, 1), attack block rate, validation pass rate).",
               f"Consumer Trust Index (CTI) = a x mean CTS + (1 - a) x PSI with a = {S['trust']['survey_weight_in_index']}. This is a proposed composite, not a validated instrument."])
    d.h1("Validity threats (from the project's methodology document)")
    d.bullets(["Internal: synthetic labels reflect generator assumptions.", "External: real fraud adapts; distribution shift is not modelled.", "Construct: 12 items are a coarse proxy for trust.",
               "Statistical: few positives in the test set make recall estimates wide."])
    return d


def d05():
    d = Doc("05_System_Architecture_and_Technology_Stack.pdf", "05 - System Architecture and Technology Stack", "Docker services, data flow, technologies",
            ["docker-compose.yml", "documentation/system_architecture.md", "documentation/technology_stack.md", "requirements.txt", "requirements-dev.txt"])
    comp = F.compose()
    d.h1("Services in docker-compose.yml")
    rows = []
    for name, sv in comp["services"].items():
        img = sv.get("image") or "built from " + sv["build"]["dockerfile"]
        ports = ", ".join(sv.get("ports", [])) if sv.get("ports") else "-"
        dep = ", ".join(sv.get("depends_on", {}).keys()) if isinstance(sv.get("depends_on"), dict) else "-"
        rows.append([name, img, ports.replace("127.0.0.1:", "").replace("${", "").replace("}", ""), dep, "yes" if "healthcheck" in sv else "no"])
    d.table(["Service", "Image", "Ports", "Depends on", "Healthcheck"], rows, widths=[1.6, 3.2, 3.2, 2.4, 1])
    d.h1("Architecture diagram")
    d.flow(["Synthetic data generators", "Worker: pipeline", "PostgreSQL results", "JSON logs -> Promtail", "Loki", "Prometheus scrapes /metrics", "cAdvisor container stats", "Grafana dashboards"],
           "Worker writes results to PostgreSQL and logs to a shared volume; Promtail ships logs to Loki; Prometheus scrapes worker, cAdvisor, Loki and Grafana; Grafana reads Prometheus, Loki and PostgreSQL.", cols=4)
    d.h1("Data flow")
    d.flow(["data/raw + data/synthetic", "validate (13 checks)", "clean -> data/interim", "features -> data/processed", "models/trained (joblib)", "report/figures + tables", "PostgreSQL tables", "Prometheus metrics"],
           "Where each artefact is written by src/pipeline.py.", cols=4)
    d.h2("Start-up order enforced by health checks")
    d.p("postgres (pg_isready) -> worker (healthy only when the metric fintech_pipeline_ready equals 1) -> jupyter. Grafana waits for prometheus, loki and postgres; promtail waits for loki.")
    d.h1("Technology stack")
    d.table(["Layer", "Technology", "Reason"], [
        ["Language", "Python 3.11 in containers", "Data-science ecosystem"], ["Data", "pandas, NumPy, SciPy, PyArrow", "Tables, statistics, Parquet"],
        ["ML", "scikit-learn, XGBoost, joblib", "Models, tuning, serialization"], ["Plots", "Matplotlib, Seaborn, Plotly", "Static and interactive figures"],
        ["Database", "PostgreSQL 16 via SQLAlchemy + psycopg2 (SQLite fallback)", "Results and metadata"], ["Metrics", "prometheus-client, Prometheus v2.53.1", "Pull-based time series"],
        ["Logs", "JSON logging, Promtail, Loki 3.1.1", "Searchable logs"], ["Dashboards", "Grafana 11.2.0 provisioning", "Dashboards and alerts as code"],
        ["Containers", "Docker Compose, cAdvisor v0.49.1", "One-command environment, container stats"], ["Research UI", "JupyterLab", "Interactive notebooks"],
        ["Quality", "pytest, Makefile", "Tests and shortcuts"]], widths=[2, 5, 3.5])
    d.h2("Dependencies declared")
    d.code(F.read("requirements.txt"))
    d.code(F.read("requirements-dev.txt"))
    d.note("Not used by design: React/HTML front end, SMOTE oversampling, deep learning, Alertmanager (listed as lab-scope omissions in the technology document).")
    return d


def d06():
    d = Doc("06_Dataset_and_Data_Preprocessing.pdf", "06 - Dataset and Data Preprocessing", "What data exists and how it is prepared",
            ["documentation/dataset_description.md", "src/data_collection/synthetic.py", "src/preprocessing/*.py", "src/feature_engineering/features.py", "survey/survey_data.csv"])
    s = F.summary()
    d.h1("Datasets")
    d.table(["Dataset", "Origin", "Notes"], [
        ["Transactions", "Seeded synthetic generator (src/data_collection/synthetic.py)", "Fraud ~2%; four stylised patterns each expressed in 75% of its cases; ~0.4% injected defects"],
        ["Security events", "Seeded synthetic generator", "18% attacks; six campaign bursts; benign background"],
        ["Survey", "Synthetic latent-factor generator; saved to survey/survey_data.csv", "Placeholder for pipeline demonstration - NOT real respondents"],
        ["ULB credit-card fraud", "Optional public dataset (user downloads to data/external)", "Code path exists (src/data_collection/external.py); no results exist unless the file is supplied"]], widths=[2, 4.5, 4])
    d.note("All numbers in this pack derived from these datasets describe the method on synthetic data. They are not evidence about real-world fraud prevalence or real consumers.")
    d.h2("Transaction columns")
    d.table(["Column", "Meaning"], [["transaction_id, customer_id", "surrogate keys"], ["timestamp", "90-day window anchored to the run date when end_date is auto"], ["amount", "log-normal around a per-customer level"],
        ["merchant_category, channel, device_type", "categoricals (11, 4, 5 values)"], ["country, home_country", "used to derive is_foreign"], ["is_new_device, ip_risk_score, velocity_1h", "risk signals"],
        ["account_age_days, auth_method", "tenure and authentication"], ["is_fraud", "label"], ["fraud_pattern", "generator pattern; analysis only, never a feature"]], widths=[3.5, 7])
    d.h1("Fraud patterns in the generator")
    d.table(["Pattern", "Share of fraud", "Signature"], [["account_takeover", "40%", "new device, foreign, high IP risk, amount x2-6, night"], ["card_testing", "25%", "tiny amounts, high velocity, web, digital goods"],
        ["synthetic_identity", "15%", "very new account, amount x3-8, new device"], ["social_engineering", "20%", "normal device and geography, large OTP-authorised transfer"]], widths=[2.5, 1.5, 6.5])
    if s:
        d.h1("Actual data volumes from the last pipeline run")
        c, t = s["cleaning"], s["transactions"]
        d.table(["Quantity", "Value"], [["Run id", s["run_id"]], ["Rows in (raw)", c["rows_in"]], ["Duplicates removed", c["duplicates_removed"]], ["Invalid rows removed", c["invalid_removed"]],
            ["Rows out (clean)", c["rows_out"]], ["Fraud rate", f"{t['fraud_rate']:.4%}"], ["Validation pass rate", f"{s['validation']['pass_rate']:.3f}"]], widths=[4, 4])
        d.h2("Validation results")
        d.table(["Check", "Passed", "Failed rows"], [[c_["check"], c_["passed"], c_["failed_count"]] for c_ in s["validation"]["checks"]], widths=[5, 1.5, 2])
        d.p("Failed checks on the raw data are expected: the generator deliberately injects missing amounts, negative amounts and duplicate rows so validation and cleaning have real work.")
    else:
        d.note("No pipeline run summary was found (models/model_metadata/last_run_summary.json), so actual data volumes are not reported here.")
    d.h1("Validation and cleaning")
    d.bullets(["src/preprocessing/validation.py: 13 checks (schema columns, minimum rows, missing ratio, missing amount, duplicate ratio and ids, positive amounts, parsable timestamps, IP risk within 0-1, binary label, channel/merchant/auth domains).",
               "src/preprocessing/cleaning.py: drop duplicate transaction ids, drop missing/non-positive amounts and unparsable timestamps, clip IP risk, fill categorical gaps with 'unknown', sort by time, return a row-accounting report; frame_hash for provenance."])
    d.h1("Feature engineering")
    from importlib import util  # noqa: F401
    d.p("src/feature_engineering/features.py builds 17 numeric and 23 one-hot features (40 total).")
    d.table(["Group", "Features"], [["Time", "hour, day_of_week, is_night, is_weekend"], ["Amount", "log_amount, amount_to_cust_avg_ratio"], ["Customer history (past only)", "cust_txn_count_prior, log_secs_since_last, amount ratio"],
        ["Risk flags", "is_new_device, is_foreign, ip_risk_score, velocity_1h, high_risk_ip, is_new_account, log_account_age"], ["Interactions", "new_device_x_foreign, night_x_high_ratio"],
        ["One-hot", "channel, merchant_category, auth_method, device_type"]], widths=[3, 7.5])
    d.p("Leakage protection: history features use cumulative sums minus the current row, so a transaction never sees its own or future values. tests/test_preprocessing.py includes a test that changes the last row and checks earlier features are unchanged.")
    d.h1("Survey privacy handling")
    d.bullets(["respondent_id is a 12-character salted SHA-256 prefix (salt from SURVEY_SALT).", "Ages are bands; no free text, IP or email fields.", "k-anonymity check and suppression on age_band x education x usage_frequency (k=5)."])
    d.h2("Storage")
    d.p("Parquet and CSV in data/raw, data/synthetic, data/interim, data/processed. These folders are git-ignored and regenerated; only the survey CSV is tracked. Files currently present:")
    d.code("\n".join(F.file_list("data/**/*")[:40]) or "(no generated data files present)")
    return d
