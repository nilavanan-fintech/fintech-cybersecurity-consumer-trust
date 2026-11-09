"""Review 2 - methodology, architecture, stack, datasets, preprocessing, initial implementation (no model results yet)."""
from theme import Deck, architecture


def build():
    d = Deck(2, "Methodology, Architecture, Data and Initial Implementation")
    d.bullets("Progress since Review 1", [
        "Objectives and research questions fixed (RQ1-RQ7, hypotheses H1-H7)",
        "Repository structure, configuration (settings.yaml) and Docker Compose skeleton created",
        "Synthetic data generators, validation, cleaning, feature engineering implemented and unit-tested",
        "PostgreSQL schema and Prometheus exporter drafted",
        "Not yet in scope for this review: model comparison, dashboards, trust results"])
    d.flow("Research methodology workflow", ["Seeded data generation", "Validation (13 checks)", "Cleaning", "Leakage-safe features",
                                              "Chronological split 70/15/15", "Tune on train, threshold on validation", "Single test evaluation", "Statistics + trust analysis"],
           cols=4, note="Chronological splitting prevents the model from learning from the future; the test set is used once.")
    architecture(d)
    d.table("Technology stack", ["Layer", "Choice", "Reason"], [
        ["Language / data", "Python, pandas, NumPy, SciPy, PyArrow", "Standard data-science stack; Parquet storage"],
        ["Machine learning", "scikit-learn, XGBoost", "LR, RF, boosting, Isolation Forest, LOF, tuning"],
        ["Visualisation", "Matplotlib, Seaborn, Plotly", "Report figures, interactive notebooks"],
        ["Database", "PostgreSQL 16 (SQLAlchemy)", "Structured results and metadata"],
        ["Monitoring", "Prometheus, Grafana, Loki + Promtail, cAdvisor", "Metrics, dashboards, logs, container health"],
        ["Packaging", "Docker Compose, Makefile, pytest", "One-command, repeatable environment"]], widths=[2.4, 4.9, 4.8])
    d.table("Dataset collection", ["Dataset", "Source", "Notes"], [
        ["Transactions", "Seeded synthetic generator", "~2% fraud, four stylised patterns expressed 75% of the time; injected defects"],
        ["Security events", "Seeded synthetic generator", "18% attacks, six campaign bursts, benign background"],
        ["Survey", "Synthetic placeholder (n~400)", "12 Likert items; replace with real consented responses"],
        ["Public benchmark", "ULB credit-card fraud (optional)", "Downloaded by user under its licence; not redistributed"]],
        widths=[2.2, 3.4, 6.5], note="Synthetic data demonstrates the method; it is not evidence about real-world fraud prevalence.")
    d.table("Data preprocessing", ["Step", "Implementation", "Why"], [
        ["Validation", "13 checks: schema, ranges, domains, duplicates, missingness", "Detect defects before modelling; exported as metrics"],
        ["Cleaning", "Drop duplicate ids and invalid/missing amounts; row accounting", "Every removal is counted and logged"],
        ["Features", "Time, amount ratios vs customer's prior mean, recency, device/geo/IP flags, one-hot", "History uses only earlier rows"],
        ["Survey privacy", "Salted-hash IDs, banded demographics, k-anonymity (k=5)", "Privacy-conscious handling"],
        ["Storage", "Parquet + CSV in data/interim, data/processed", "Typed, compact, portable"]], widths=[1.9, 5.8, 4.4])
    d.bullets("Initial implementation progress", [
        "src/ modules: data_collection, preprocessing, feature_engineering, database, metrics",
        "Unit tests cover validation, cleaning, leakage-freedom (changing a future row leaves earlier features unchanged) and reproducibility",
        "database/schema.sql with results, metadata, quality-check and trust tables",
        "docker-compose.yml with health-checked service ordering",
        "Pending: model training, anomaly detection, trust scoring, dashboards (Review 3)"],
        note="Evidence: repository code and tests. No model performance is reported at this stage.")
    d.table("Evaluation plan (fixed before experiments)", ["Aspect", "Plan"], [
        ["Metrics", "Accuracy (reported, not trusted), precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, false-positive rate"],
        ["Uncertainty", "Bootstrap 95% CI; McNemar test for paired model comparison"],
        ["Trust", "Cronbach's alpha, Spearman, OLS, Kruskal-Wallis, Mann-Whitney; Bonferroni across hypotheses"],
        ["Reproducibility", "Seeds, data hash and library versions stored with each model"]], widths=[2.4, 9.7])
    d.save("review_2.pptx")


if __name__ == "__main__":
    build()
