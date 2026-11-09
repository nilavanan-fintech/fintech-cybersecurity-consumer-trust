# Chapter 5 - Results

> **Provenance.** All numbers below come from pipeline run `run_20261109_061947_57b9` (seed 42, default `config/settings.yaml`: 60,000 generated transactions,
> `tuning.n_iter = 8`, 3-fold CV). Full tables: `report/tables/results_summary.md`; raw summary: `models/model_metadata/last_run_summary.json`.
> **Data are synthetic** (transactions, security events and survey). Results validate the method; they are not evidence about real fraud or real consumers.
> Single seed, no repeats - treat differences between close models as tentative.

## 5.1 Data and validation
* 60,120 rows generated; 120 duplicate ids and 318 invalid/missing-amount rows removed → **59,682** clean rows; labelled fraud rate **2.02 %**.
* Validation flagged the deliberately injected defects (missing amounts, duplicate ids, non-positive amounts), confirming the checks work.
* Chronological split 70/15/15; the test partition contains **174** fraud cases (TP + FN for any model), so recall estimates carry wide uncertainty.

## 5.2 Supervised and unsupervised detectors (test set, validation-tuned thresholds)

| Model | Precision | Recall | F1 | ROC-AUC | PR-AUC | FPR |
|---|---|---|---|---|---|---|
| Logistic Regression | 0.883 | 0.563 | 0.688 | 0.872 | 0.666 | ~0.001 |
| Random Forest | 0.928 | 0.667 | 0.776 | 0.903 | 0.741 | ~0.001 |
| **XGBoost (champion by PR-AUC)** | **0.982** | 0.626 | 0.765 | 0.885 | **0.743** | ~0.000 |
| Isolation Forest (unsupervised) | 0.365 | 0.437 | 0.398 | 0.780 | 0.400 | 0.015 |
| Local Outlier Factor (unsupervised) | 0.187 | 0.287 | 0.226 | 0.683 | 0.116 | 0.025 |

Observations (not over-interpreted):
* Tree ensembles beat the linear baseline on PR-AUC; XGBoost and Random Forest are nearly tied on PR-AUC (0.743 vs 0.741). Random Forest has the higher recall, F1 and ROC-AUC; XGBoost the higher precision. Which is "best" depends on the metric chosen - the champion rule (PR-AUC) is stated in advance in the methodology.
* McNemar test, XGBoost vs Logistic Regression: b = 30, c = 8, χ² = 11.6, p ≈ 0.0007 - their error patterns differ significantly on this test set.
* Champion ROC-AUC 95 % bootstrap CI: **[0.847, 0.918]**.
* Unsupervised detectors rank fraud above chance (ROC-AUC 0.78 / 0.68) but with far lower precision and a false-positive rate of 1.5-2.5 %, i.e. much more customer friction, as expected without labels.
* Accuracy is not discussed as a selection criterion because of the 2 % base rate.

## 5.3 Risk tiers (XGBoost, test set)

| Tier | Transactions | Frauds | Observed fraud rate | Action |
|---|---|---|---|---|
| low | 3 | 0 | 0.0 % | allow |
| medium | 7,871 | 37 | 0.47 % | step-up authentication |
| high | 912 | 12 | 1.32 % | manual review |
| critical | 167 | 125 | 74.9 % | block + alert |

Fraud rate increases monotonically across tiers, but the fixed cut-offs (0.05 / 0.30 / 0.70) put almost everything in *medium*: because the models use class weighting, their raw probabilities are not calibrated. **Probability calibration is not implemented** and is a clear improvement (Chapter 6).

## 5.4 Security-event analysis
Isolation Forest (fit without labels on the first 70 % of time) reaches ROC-AUC **0.994** against known attacks; the attack block rate in the generated data is **0.797**. The high AUC reflects how conspicuous the synthetic attack signatures (failed attempts, bytes out) are by construction; real telemetry would be harder.

## 5.5 Consumer trust (synthetic survey, n = 355 after k-anonymity suppression)
* Mean Consumer Trust Score **56.6 / 100**; Platform Security Index **79.8**; Consumer Trust Index (0.6·CTS + 0.4·PSI) **65.8**.
* Segments: Low 122, Moderate 178, High 55. Cronbach's α (all items) **0.906**.
* Spearman ρ with CTS: digital literacy +0.48, MFA use +0.43, past fraud experience −0.22; OLS R² = 0.36.
* These directions were built into the generator, so recovering them shows the analysis pipeline works; it is not a finding about people.

## 5.6 Pipeline and monitoring
All pipeline stages are timed and exported as Prometheus metrics (full run ≈ 245 s on the development machine; tuning dominates). Grafana dashboards query these metrics, PostgreSQL views and Loki logs. See Chapter 4 and `documentation/dashboard_guide.md`.

## 5.7 Reproducibility
The same seed regenerates the same data values (dates follow the run date when `end_date: auto`). Model metadata JSON stores parameters, thresholds, features, data hash and library versions.
