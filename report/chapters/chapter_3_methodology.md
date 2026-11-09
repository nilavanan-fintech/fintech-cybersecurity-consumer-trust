# Chapter 3 - Methodology

The full protocol is in [`documentation/methodology.md`](../../documentation/methodology.md); summary:

* **Data:** seeded synthetic transactions (≈2 % fraud, four patterns), security events with attack campaigns, synthetic survey (n≈400); optional ULB credit-card dataset.
* **Pre-processing:** 13 validation checks, deduplication, invalid-row removal, Parquet/CSV storage.
* **Features:** 17 numeric + 23 one-hot features; history features use only earlier data.
* **Split:** chronological 70/15/15; tuning by randomised search on training data; threshold chosen on validation; test used once.
* **Models:** Logistic Regression, Random Forest, XGBoost; Isolation Forest, LOF (unsupervised).
* **Metrics:** accuracy, precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, FPR; bootstrap CI; McNemar.
* **Trust:** CTS from 12 Likert items (5 dimensions), Cronbach's α, Spearman/OLS/Kruskal; PSI from measured security; CTI = 0.6·CTS + 0.4·PSI with sensitivity analysis.
* **Ethics/privacy:** synthetic or licensed data only; pseudonymised, banded, k-anonymous survey; ethics approval required for real collection.
