"""Review 4 - completed implementation, results, model comparison, metrics, dashboards, conclusions, limitations, future work.
All figures/numbers are read from real pipeline output."""
from theme import ROOT, Deck, architecture, load_summary

FIG = ROOT / "report" / "figures"


def build():
    s = load_summary()
    m = s["models"]; R = m["results"]; names = list(R); sup = [n for n in names if m["types"][n] == "supervised"]
    d = Deck(4, "Results, Model Comparison, Dashboards and Conclusions")
    d.table("Completed implementation", ["Component", "Status"], [
        ["Pipeline (collect to report, 14 timed stages)", "Complete"], ["Models: LR, RF, XGBoost, Isolation Forest, LOF", "Complete"],
        ["Risk tiers, trust scoring, statistics", "Complete"], ["PostgreSQL schema, views, persistence", "Complete"],
        ["Prometheus exporter, Loki logging, 7 Grafana dashboards, alert rules", "Complete"], ["16 notebooks, pytest suite, Docker Compose, Makefile", "Complete"],
        ["Real survey data / ethics approval", "Pending - bundled survey is synthetic"]], widths=[8.6, 3.5])
    architecture(d, "Final system architecture")
    d.bar_chart("Model comparison: PR-AUC, ROC-AUC, F1 (test set)", names,
                {"PR-AUC": [R[n]["pr_auc"] for n in names], "ROC-AUC": [R[n]["roc_auc"] for n in names], "F1": [R[n]["f1"] for n in names]},
                f"Run {s['run_id']}, seed {s['seed']}. Champion (highest PR-AUC among supervised): {m['champion']}.")
    d.table("Performance metrics (test set)", ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "PR-AUC", "FPR"],
            [[n, f"{R[n]['accuracy']:.4f}", f"{R[n]['precision']:.3f}", f"{R[n]['recall']:.3f}", f"{R[n]['f1']:.3f}", f"{R[n]['roc_auc']:.3f}",
              f"{R[n]['pr_auc']:.3f}", f"{R[n]['false_positive_rate']:.4f}"] for n in names],
            widths=[2.9, 1.4, 1.4, 1.3, 1.2, 1.3, 1.3, 1.3], size=12,
            note="Accuracy is high for any model on ~2% fraud and is not a selection criterion; PR-AUC and FPR are.")
    ch = m["champion"]; lo, hi = m["champion_roc_auc_ci95"]
    d.table("Statistical comparison", ["Item", "Result"], [
        ["Champion", ch], ["Champion ROC-AUC 95% bootstrap CI", f"[{lo:.3f}, {hi:.3f}]"],
        ["McNemar champion vs Logistic Regression", "n/a" if not m["mcnemar_vs_lr"] else f"chi2={m['mcnemar_vs_lr']['chi2']:.2f}, p={m['mcnemar_vs_lr']['p_value']:.4f}"],
        ["Confusion (champion)", f"TP={R[ch]['tp']} FP={R[ch]['fp']} FN={R[ch]['fn']} TN={R[ch]['tn']}"]], widths=[5.6, 6.5])
    d.table("Risk tiers (champion, test set)", ["Tier", "Transactions", "Frauds", "Observed fraud rate", "Action"],
            [[r["tier"], int(r["transactions"]), int(r["frauds"]), "-" if r["observed_fraud_rate"] is None else f"{r['observed_fraud_rate']:.3f}", r["action"]] for r in m["risk_tiers"]],
            widths=[1.8, 2.2, 1.8, 2.8, 3.5])
    for f, cap in (("confusion_matrices.png", "Confusion matrices at validation-tuned thresholds."), ("consumer_trust_overview.png", "Consumer trust (synthetic survey): score distribution, dimensions, correlations."),
                   ("security_overview.png", "Security events and attack types.")):
        d.image(f.replace("_", " ").replace(".png", "").title(), FIG / f, cap)
    sec, t = s["security"], s["trust"]
    d.table("Security and trust results", ["Quantity", "Value"], [
        ["Attack block rate", f"{sec['attack_block_rate']:.3f}"], ["Isolation Forest ROC-AUC vs known attacks", f"{sec['anomaly_roc_auc']:.3f}"],
        ["Mean Consumer Trust Score", f"{t['mean_trust_score']:.1f}"], ["Platform Security Index", f"{t['platform_security_index']:.1f}"],
        ["Consumer Trust Index", f"{t['consumer_trust_index']:.1f}"], ["Cronbach alpha", f"{t['cronbach_alpha']['overall']:.3f}"]], widths=[7.0, 5.1],
        note="Survey is synthetic; trust values demonstrate the method and are not findings about real consumers.")
    shots = [("grafana_overview.png", "Grafana: Research Overview"), ("grafana_fraud.png", "Grafana: Transaction & Fraud Analytics"),
             ("grafana_models.png", "Grafana: ML Model Performance"), ("grafana_infra.png", "Grafana: Docker Infrastructure")]
    found = 0
    for f, cap in shots:
        if (ROOT / "review" / "assets" / f).exists():
            d.image(cap, ROOT / "review" / "assets" / f, "Screenshot captured from the running stack."); found += 1
    if not found:
        d.bullets("Grafana dashboard demonstration", ["Live demo: Overview, Pipeline Monitoring, Fraud, Model Performance, Trust, Infrastructure",
                  "Add screenshots as review/assets/grafana_*.png and re-run review/scripts/build_all.py"], note="No screenshots were available when this deck was generated.")
    d.bullets("Conclusions", [
        f"A reproducible, observable platform links fraud/anomaly detection with a consumer trust measure ({len(sup)} supervised + 2 unsupervised detectors)",
        "Tree ensembles are compared with a linear baseline using PR-AUC, recall and false-positive rate rather than accuracy",
        "Unsupervised detectors are useful without labels but are compared separately from supervised models",
        "Grafana shows live computed metrics, logs and database results for the entire experiment"])
    d.two_col("Limitations", "Data and validity", ["Synthetic transactions encode our assumptions", "Bundled survey is synthetic", "Few positives in test set widen uncertainty", "No concept drift modelled"],
              "Method", ["Trust Index is a proposal, not validated", "Single dataset family and limited tuning budget", "Replay stream is not production traffic", "Alertmanager not deployed"])
    d.bullets("Future enhancements", ["Run on the public ULB dataset and other licensed data; repeat over many seeds", "Real ethics-approved survey; factor analysis and index validation",
                                       "Add calibration, cost-sensitive thresholds, explainability (SHAP)", "Drift monitoring and scheduled retraining; Alertmanager notifications",
                                       "Combine unsupervised scores with supervised features"])
    d.save("review_4.pptx")


if __name__ == "__main__":
    build()
