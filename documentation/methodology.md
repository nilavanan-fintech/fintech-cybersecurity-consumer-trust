# Methodology

## 1. Research design
Design-science / experimental computer-science study with a quantitative survey component. Experiments are
deterministic (seeded) and logged (run id, data hash, library versions are stored with every model).

## 2. Data
See [dataset_description.md](dataset_description.md). Synthetic generators encode *stylised* fraud patterns (account takeover,
card testing, synthetic identity, social engineering) expressed 75 % of the time so classes overlap. Defects (missing, duplicate,
negative amounts) are injected to exercise validation.

## 3. Pre-processing
Validation (13 checks) → cleaning (dedupe, drop invalid) → Parquet/CSV storage. Every removal is counted and published.

## 4. Feature engineering
Time features (hour, weekday, night), amount transforms, ratios against the customer's **prior** mean (cumulative sums minus the
current row), time since last transaction, device/geo/IP-risk flags, interactions, one-hot encodings with fixed domains.
A unit test and notebook 02 prove that changing a future row does not change earlier features (no temporal leakage).

## 5. Experimental protocol
* **Split:** chronological 70/15/15 (train/validation/test). Random shuffling would leak future behaviour.
* **Tuning:** `RandomizedSearchCV` (Bergstra & Bengio, 2012) on training data, stratified k-fold, score = average precision.
* **Imbalance:** `class_weight` / `scale_pos_weight`; no SMOTE, to keep probabilities usable for risk tiers.
* **Threshold:** F1-optimal on validation, applied once to test.
* **Models & rationale:** Logistic Regression (interpretable baseline), Random Forest (Breiman, 2001; non-linear, robust),
  XGBoost (Chen & Guestrin, 2016; strong tabular learner), Isolation Forest (Liu et al., 2008) and LOF (Breunig et al., 2000) as
  label-free detectors that mirror settings where labels are delayed.
* **Metrics:** accuracy (reported but not trusted under imbalance), precision, recall, F1, ROC-AUC, PR-AUC (Saito & Rehmsmeier,
  2015), confusion matrix, false-positive rate. Uncertainty: bootstrap 95 % CI; model difference: McNemar test.
* **Risk classification:** probability → {low, medium, high, critical} → {allow, step-up auth, manual review, block}; observed fraud rate per tier checks monotonicity.

## 6. Security-event analysis
Synthetic telemetry with attack campaigns. Isolation Forest fit on the first 70 % of time with *no labels*; labels used only for evaluation.

## 7. Consumer trust measurement
* **Instrument:** 12 five-point Likert items (11 positive, 1 reverse-coded) in five dimensions - perceived security, privacy
  assurance, transparency, reliability, behavioural intent - informed by trust-in-e-commerce research (McKnight et al., 2002; Gefen et al., 2003; Pavlou, 2003).
* **Score:** CTS = Σ wᵢ · dimension_i rescaled to 0-100; segments Low < 50 ≤ Moderate < 75 ≤ High (configurable).
* **Reliability:** Cronbach's α (Cronbach, 1951). **Drivers:** Spearman correlation, OLS on standardised predictors, Kruskal-Wallis, Mann-Whitney.
* **Platform Security Index (PSI):** mean of detection recall, (1 − 10·FPR, floored at 0), attack block rate, validation pass rate.
* **Consumer Trust Index (CTI):** a·mean(CTS) + (1−a)·PSI, a = 0.6. The composite and its weights are a *proposal*; notebook 05 reports sensitivity to a and to dimension weights.
* **Privacy:** salted-hash pseudonyms, banded demographics, no free text/IP/email, k-anonymity (k = 5) check and suppression.

## 8. Statistical analysis
α = 0.05, Bonferroni across the hypothesis family; effect sizes (Cramér's V, rank-biserial) accompany p-values.

## 9. Reproducibility & operations
Seeds in `config/settings.yaml`; data hash and library versions in model metadata; one-command Docker deployment; tests in `tests/`.
Monitoring methodology: see [system_architecture.md](system_architecture.md) §3.

## 10. Validity threats
*Internal:* synthetic labels reflect generator assumptions. *External:* real fraud adapts to defences; distribution shift is not modelled.
*Construct:* a 12-item scale is a coarse proxy for trust. *Statistical:* few positives in the test set make recall estimates wide (see CIs).
