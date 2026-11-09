# Research questions and hypotheses

| ID | Research question | Evidence produced | Where |
|---|---|---|---|
| RQ1 | Which supervised model gives the best fraud-detection trade-off on imbalanced transaction data, judged by PR-AUC, recall and false-positive rate? | metric table, CIs, McNemar | notebook 03/07, Ch. 5 |
| RQ2 | How far can label-free anomaly detectors (Isolation Forest, LOF) get compared with supervised learning? | ROC/PR-AUC, precision@k | notebook 04 |
| RQ3 | What do detection errors cost the consumer (false-positive rate, flagged legitimate customers) at different thresholds? | threshold sweep, risk tiers | notebook 07 |
| RQ4 | Which behavioural/transaction signals characterise each fraud pattern, and which patterns evade detection? | signature heatmap, recall by pattern | analysis/fraud_pattern_analysis |
| RQ5 | How do consumers perceive FinTech cybersecurity, and which respondent factors (MFA use, past fraud, digital literacy, age) relate to trust? | CTS, correlations, OLS, tests | survey/, analysis/consumer_trust_analysis |
| RQ6 | Can perceived trust and measured security be combined into a stable index, and how sensitive is it to design choices? | CTI, sensitivity analysis | notebook 05 |
| RQ7 | Can research-pipeline health and model quality be monitored continuously with open-source observability tooling? | Grafana dashboards, alerts | dashboard/, Ch. 4 |

## Hypotheses (tested on the bundled synthetic data; re-test on real data)
* **H1** Fraudulent transaction amounts differ from legitimate ones (Mann-Whitney).
* **H2** Channel is associated with fraud (χ²). **H3** Authentication method is associated with fraud (χ²).
* **H4** Trust differs across age bands (Kruskal-Wallis). **H5** Respondents with past fraud experience report lower trust (Mann-Whitney).
* **H6** Gradient-boosted trees achieve higher PR-AUC than Logistic Regression (bootstrap CI + McNemar).
* **H7** MFA users report higher perceived security than non-users (Spearman, association only).

Hypotheses are directional expectations drawn from the literature, not claims about the synthetic generator being "right".
