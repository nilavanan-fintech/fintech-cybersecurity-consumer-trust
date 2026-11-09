# Survey results

> **These results are computed from SYNTHETIC respondents** (latent-factor generator, `src/data_collection/synthetic.py`). They demonstrate the analysis
> pipeline. Replace `survey_data.csv` with real, ethics-approved, consented responses and re-run `make pipeline` before reporting any finding.

Run `run_20261109_061947_57b9`, seed 42. 400 respondents generated; 45 suppressed by k-anonymity (k = 5) → **355** analysed.

| Quantity | Value |
|---|---|
| Mean Consumer Trust Score (0-100) | 56.6 |
| Segments | Low 122 · Moderate 178 · High 55 |
| Cronbach's α, all 12 items | 0.906 |
| Spearman ρ with trust: digital literacy / MFA use / past fraud | +0.48 / +0.43 / −0.22 |
| OLS R² (three predictors) | 0.36 |
| Smallest quasi-identifier group | 5 |

Per-dimension means, item means, group means and tests: `models/model_metadata/last_run_summary.json`, `report/tables/`, `survey_analysis.ipynb`.
The associations are cross-sectional and planted by the generator; no causal or real-world claim is made.
