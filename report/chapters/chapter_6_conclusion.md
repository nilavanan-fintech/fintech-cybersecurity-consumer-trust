# Chapter 6 - Conclusion, limitations and future work

## 6.1 Conclusions
1. A reproducible, containerised platform now connects transaction fraud detection, security-event anomaly detection and consumer-trust measurement, and exposes the experiment through Prometheus, Loki, PostgreSQL and Grafana.
2. On the synthetic data, boosted and bagged trees outperform a linear baseline on PR-AUC (RQ1); unsupervised detectors are clearly weaker and produce more false positives (RQ2).
3. Reporting false-positive rate and risk-tier outcomes makes the consumer cost of detection explicit (RQ3). The risk-tier cut-offs need calibration before use.
4. The survey pipeline (scoring, reliability, drivers, privacy checks) works end to end on synthetic respondents (RQ5); the combined Consumer Trust Index is computed and sensitivity-tested but not validated (RQ6).
5. Monitoring is driven by computed metrics rather than static panels (RQ7).

## 6.2 Limitations
* Synthetic data embed the authors' assumptions; no concept drift; high security-event AUC reflects conspicuous synthetic signatures.
* Synthetic survey - **no real respondents and no recorded ethics approval**; any trust figures are demonstration values.
* Trust Index and Platform Security Index weights are design choices without psychometric validation.
* Single seed and a small tuning budget (`n_iter = 8`); 174 test-set fraud cases give wide intervals; close models (XGBoost vs Random Forest) cannot be ranked firmly.
* Class-weighted models are uncalibrated, so fixed probability cut-offs misplace transactions across risk tiers.
* The live stream is a replay of held-out data, not production traffic; Alertmanager is not deployed.
* The public ULB credit-card benchmark has not been run (file not supplied).
* Bibliography entries have not been verified against publisher records.

## 6.3 Future enhancements
* Calibrate probabilities (isotonic / Platt) and derive risk-tier thresholds from cost.
* Repeat experiments over many seeds; run the ULB benchmark; add SHAP explanations.
* Collect a real, ethics-approved survey; run a pilot, factor analysis and test-retest to validate the index.
* Drift monitoring and scheduled retraining; Alertmanager notifications.
* Use unsupervised scores as features for supervised models; add behavioural-biometric signals for social-engineering fraud.
