"""Review 1 - introduction, problem, objectives, literature survey, research gap, proposed solution (no results yet)."""
from theme import Deck, architecture  # noqa: F401


def build():
    d = Deck(1, "Introduction, Literature Survey and Proposed Solution")
    d.bullets("Agenda", ["Introduction and motivation", "Problem statement", "Aim and objectives", "Literature survey",
                         "Research gap", "Proposed solution and plan", "Ethics and scope"], size=22)
    d.bullets("Introduction and motivation", [
        "FinTech moves payments, identity and personal data through software that is attacked continuously",
        "Providers invest in fraud detection and threat monitoring",
        "Adoption depends on consumer trust, which reflects perceived as well as actual security",
        ("Trust is multi-dimensional: competence, integrity, benevolence (McKnight et al., 2002)", ),
        "Security teams and trust researchers rarely share one reproducible evidence base"])
    d.bullets("Problem statement", [
        "Fraud-detection studies optimise predictive metrics, often on a single dataset and with accuracy-style reporting",
        "Consumer-trust studies rely on surveys that are disconnected from measured security performance",
        "Detection errors have a consumer cost: false positives block legitimate customers",
        "Research pipelines are seldom observable: results are not monitored or easily reproduced"],
        note="Core question: how do measurable cybersecurity capabilities relate to consumer trust, and can the experiment itself be monitored?")
    d.table("Aim and objectives", ["ID", "Objective"], [
        ["O1", "Reproducible pipeline for transaction and security-event data (synthetic + optional public)"],
        ["O2", "Compare supervised and unsupervised fraud/anomaly detectors with imbalance-aware metrics"],
        ["O3", "Quantify the operational cost of detection errors (false-positive rate)"],
        ["O4", "Measure consumer trust with a documented, privacy-conscious survey"],
        ["O5", "Propose and stress-test a composite Consumer Trust Index"],
        ["O6", "Instrument the pipeline so Grafana shows real collected data"]], widths=[1.0, 11.1])
    d.table("Literature survey", ["Theme", "Key works", "Take-away for this project"], [
        ["ML fraud detection", "Ngai et al. 2011; Bhattacharyya et al. 2011; Chen & Guestrin 2016", "Ensembles/boosting are strong baselines"],
        ["Feature engineering", "Bahnsen et al. 2016", "History/behavioural aggregates matter"],
        ["Imbalance and metrics", "Davis & Goadrich 2006; Saito & Rehmsmeier 2015; Dal Pozzolo et al. 2015", "Use PR-AUC; avoid resampling that distorts probabilities"],
        ["Anomaly detection", "Liu et al. 2008; Breunig et al. 2000; Chandola et al. 2009", "Label-free detectors for delayed labels"],
        ["Trust in e-commerce", "McKnight 2002; Gefen 2003; Pavlou 2003; Davis 1989", "Multi-dimensional trust constructs"],
        ["Measurement/privacy", "Cronbach 1951; Likert 1932; Sweeney 2002", "Reliability checks; k-anonymity"]],
        widths=[2.4, 5.6, 4.1], size=12, note="References: report/references.bib (entries to be verified against publisher records).")
    d.two_col("Research gap", "What exists", ["Strong fraud models evaluated in isolation", "Trust surveys without security telemetry",
                                              "Monitoring treated as an operations topic, not a research instrument"],
              "What is missing", ["Joint view of measured security and perceived trust", "Transparent, sensitivity-tested composite index",
                                   "Reproducible, observable research platform suitable for replication"])
    d.flow("Proposed solution - research workflow", ["Data (synthetic / public)", "Validate + clean", "Features", "Train + tune models",
                                                       "Evaluate + risk tiers", "Survey + trust score", "Trust index", "Metrics, logs, dashboards"],
           cols=4, note="Python pipeline + PostgreSQL + JupyterLab, monitored with Prometheus, Loki and Grafana; all in Docker Compose.")
    architecture(d, "Proposed solution - planned architecture")
    d.table("Plan and expected deliverables", ["Month", "Focus", "Deliverable"], [
        ["1", "Introduction, literature, gap, design", "This review; repository skeleton"],
        ["2", "Methodology, architecture, data, preprocessing", "Generators, validation, cleaning, features, containers"],
        ["3", "Models, anomaly detection, trust scoring, dashboards", "Training pipeline, metrics exporter, Grafana"],
        ["4", "Results, comparison, conclusions", "Evaluation, report chapters, final demo"]], widths=[1.2, 5.6, 5.3],
        note="Status at Review 1: planning and design only; no experimental results are claimed in this review.")
    d.bullets("Ethics, scope and risks", [
        "Security experiments use synthetic data in an isolated environment, or licensed public datasets; no production systems are probed",
        "Survey: voluntary, no direct identifiers, banded demographics, k-anonymity; ethics approval required before real data collection",
        "Risk: synthetic data encodes our assumptions - results validate the method, not real prevalence",
        "Risk: the trust index is a proposal, not a validated instrument - sensitivity analysis planned"])
    d.save("review_1.pptx")


if __name__ == "__main__":
    build()
