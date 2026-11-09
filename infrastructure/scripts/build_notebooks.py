"""Generate the research notebooks (sources only; run `make notebooks` to execute and store outputs).

Notebooks read the REAL artefacts produced by the pipeline via src/notebook_utils.py.
"""
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]

SETUP = '''import sys, pathlib, warnings
warnings.filterwarnings("ignore")
_r = pathlib.Path.cwd().resolve()
while not (_r / "config" / "settings.yaml").exists() and _r != _r.parent:
    _r = _r.parent
sys.path.insert(0, str(_r))                      # makes `import src...` work from any folder
import numpy as np, pandas as pd, matplotlib.pyplot as plt, seaborn as sns
import plotly.express as px
from src.notebook_utils import *
sns.set_theme(style="whitegrid"); pd.set_option("display.max_columns", 40, "display.width", 140)
print("project root:", _r)'''


def md(t):
    return nbf.v4.new_markdown_cell(t.strip())


def code(t):
    return nbf.v4.new_code_cell(t.strip())


def write(path, cells):
    nb = nbf.v4.new_notebook()
    nb.cells = [code(SETUP)] + cells
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(nb, p)
    print("wrote", path)


# =============================== analysis/ ====================================================
write("analysis/exploratory_data_analysis.ipynb", [
    md("# Exploratory data analysis\n**Goal:** understand the cleaned transaction data before modelling - structure, class imbalance, and which raw attributes relate to fraud.\n\n> All data is synthetic (isolated environment). Patterns are stylised, so conclusions concern the *method*, not real-world prevalence."),
    code("df = load_clean()\nprint(df.shape); df.head()"),
    code("df.dtypes.to_frame('dtype').join(df.isna().sum().rename('missing')).T"),
    md("## Class imbalance\nFraud is rare, therefore accuracy is misleading; the project reports precision, recall, F1, ROC-AUC, PR-AUC and false-positive rate."),
    code("vc = df.is_fraud.value_counts(); print(vc.to_dict(), f'fraud rate = {df.is_fraud.mean():.3%}')\nprint('A model that predicts \"legit\" always has accuracy', round(1-df.is_fraud.mean(), 4))"),
    code("fig, ax = plt.subplots(1, 3, figsize=(16, 4))\nsns.histplot(df, x='amount', hue='is_fraud', log_scale=True, stat='density', common_norm=False, ax=ax[0]); ax[0].set_title('Amount (log) by class')\nsns.barplot(data=df, x='channel', y='is_fraud', ax=ax[1], errorbar=None); ax[1].set_title('Fraud rate by channel')\nsns.barplot(data=df, x='auth_method', y='is_fraud', ax=ax[2], errorbar=None); ax[2].set_title('Fraud rate by authentication')\nplt.tight_layout()"),
    code("num = ['amount','ip_risk_score','velocity_1h','account_age_days','is_new_device']\ndf[num].corrwith(df.is_fraud, method='spearman').sort_values().to_frame('spearman vs is_fraud')"),
    code("px.scatter(df.sample(5000, random_state=1), x='ip_risk_score', y='amount', color=df.sample(5000, random_state=1).is_fraud.astype(str), log_y=True, opacity=.6, title='IP risk vs amount (5k sample)')"),
    md("**Take-aways** - fraud concentrates in high IP-risk, new-device, high-velocity and unusual-hour activity; no single raw attribute separates the classes, motivating engineered features (notebook 02) and ensemble models (03, 06)."),
])

write("analysis/data_quality_analysis.ipynb", [
    md("# Data quality analysis\nWe load the **raw** extract (including deliberately injected defects), run the validation suite, then show what cleaning did."),
    code("from src.preprocessing.validation import validate_transactions, validation_pass_rate\nfrom src.preprocessing.cleaning import clean_transactions\nraw = load_raw()\nchecks = pd.DataFrame(validate_transactions(raw, CFG)); checks"),
    code("print('pass rate:', round(validation_pass_rate(checks.to_dict('records')), 3))\nchecks[~checks.passed][['check','failed_count','detail']]"),
    code("clean, rep = clean_transactions(raw); pd.Series(rep).to_frame('rows')"),
    code("after = pd.DataFrame(validate_transactions(clean, CFG))\npd.concat([checks.set_index('check').failed_count.rename('before'), after.set_index('check').failed_count.rename('after')], axis=1)"),
    code("fig, ax = plt.subplots(figsize=(8, 3))\nraw.isna().mean().mul(100).loc[lambda s: s > 0].plot.barh(ax=ax); ax.set(title='Missing values in raw data (%)')"),
    md("Residual `fraud_pattern`/label columns are retained for analysis only; they are **never** model features (see `feature_names()`)."),
])

write("analysis/transaction_analysis.ipynb", [
    md("# Financial transaction analysis\nVolumes, temporal rhythm, customer concentration and the monetary impact of fraud."),
    code("df = load_clean(); df['timestamp'] = pd.to_datetime(df.timestamp); df['day'] = df.timestamp.dt.date; df['hour'] = df.timestamp.dt.hour; df['dow'] = df.timestamp.dt.day_name()"),
    code("daily = df.groupby('day').agg(n=('amount','size'), value=('amount','sum'), frauds=('is_fraud','sum'))\nfig, ax = plt.subplots(1, 2, figsize=(14, 3.8)); daily.n.plot(ax=ax[0], title='Transactions per day'); daily.frauds.plot(ax=ax[1], color='crimson', title='Frauds per day')"),
    code("pt = df.pivot_table(index='dow', columns='hour', values='amount', aggfunc='size').reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])\nsns.heatmap(pt, cmap='mako'); plt.title('Transaction volume: weekday x hour')"),
    code("df.groupby('channel').amount.describe(percentiles=[.5,.9,.99]).round(2)"),
    code("per_c = df.groupby('customer_id').amount.sum().sort_values(ascending=False)\nshare = per_c.cumsum() / per_c.sum()\nprint('Top 10% of customers account for', f'{share.iloc[int(len(share)*.1)]:.1%}', 'of value')"),
    code("impact = df.groupby('is_fraud').amount.agg(['count','sum','mean','median']); impact"),
    code("px.treemap(df[df.is_fraud==1], path=['channel','merchant_category'], values='amount', title='Where fraud value concentrates')"),
])

write("analysis/cybersecurity_threat_analysis.ipynb", [
    md("# Cybersecurity threat analysis\nSynthetic security-event telemetry with embedded attack *campaigns*; an unsupervised Isolation Forest (fit on the first 70% of time, no labels) is evaluated against known attack labels."),
    code("ev = load_events(); ev['timestamp'] = pd.to_datetime(ev.timestamp); print(ev.shape); ev.head(3)"),
    code("atk = ev[ev.is_attack==1]\nsummary = atk.groupby('event_type').agg(events=('is_attack','size'), blocked=('blocked','mean'), mean_failed=('failed_attempts','mean'), mean_resp=('response_time_s','mean')).round(3).sort_values('events', ascending=False); summary"),
    code("hourly = ev.set_index('timestamp').resample('1h').is_attack.sum()\nfig, ax = plt.subplots(figsize=(14, 3.5)); hourly.plot(ax=ax, lw=.8); ax.set(title='Attack events per hour - campaigns appear as bursts')"),
    code("from sklearn.metrics import roc_auc_score, precision_recall_curve, average_precision_score\nprint('ROC-AUC', round(roc_auc_score(ev.is_attack, ev.anomaly_score), 3), '| PR-AUC', round(average_precision_score(ev.is_attack, ev.anomaly_score), 3))\nprint('Flagged:', int(ev.flagged.sum()), '| precision of flags:', round(ev[ev.flagged].is_attack.mean(), 3), '| recall:', round(ev[ev.is_attack==1].flagged.mean(), 3))"),
    code("fig, ax = plt.subplots(1, 2, figsize=(13, 4))\nsns.kdeplot(data=ev, x='anomaly_score', hue='is_attack', common_norm=False, ax=ax[0]); ax[0].set_title('Isolation Forest score by class')\nrecall_by_type = atk.groupby('event_type').flagged.mean().sort_values(); recall_by_type.plot.barh(ax=ax[1]); ax[1].set_title('Share of attacks flagged, by type')"),
    code("pd.crosstab(atk.source_country, atk.event_type)"),
    md("**Reading:** high-volume, high-failure attacks (brute force, credential stuffing) are easy for an unsupervised detector; low-footprint attacks (phishing click, API abuse) hide inside benign behaviour - an honest limitation to discuss in the viva."),
])

write("analysis/consumer_trust_analysis.ipynb", [
    md("# Consumer trust analysis\nFrom Likert responses to the Consumer Trust Score (CTS), reliability and drivers. Survey data here is **synthetic** until real consented responses replace `survey/survey_data.csv`."),
    code("from src.trust_scoring.scoring import score_respondents, reliability_report, dimension_scores\nfrom src.model_evaluation import statistics as st\nsv = load_survey(); sc = score_respondents(sv, CFG); full = sv.merge(sc[['respondent_id','trust_score','segment']], on='respondent_id')\nsc.describe().round(1)"),
    code("pd.Series(reliability_report(sv)).round(3).to_frame('Cronbach alpha')"),
    code("fig, ax = plt.subplots(1, 2, figsize=(13, 4))\nsns.histplot(sc.trust_score, kde=True, ax=ax[0]); sc.segment.value_counts().reindex(['Low','Moderate','High']).plot.bar(ax=ax[1], color=['#c1121f','#e9c46a','#2a9d8f'])"),
    code("st.correlation_with_p(full, 'trust_score', ['uses_mfa','experienced_fraud','digital_literacy'])"),
    code("res = st.ols(full[['uses_mfa','experienced_fraud','digital_literacy']], full.trust_score); print('R2 =', round(res.attrs['r2'], 3)); res.round(4)"),
    code("print(st.kruskal(full, 'trust_score', 'age_band')); sns.boxplot(data=full, x='age_band', y='trust_score', order=['18-24','25-34','35-44','45-54','55+'])"),
    md("Interpretation guardrail: coefficients are *associations* on standardised predictors; the survey is cross-sectional, so no causal claim (e.g. that MFA *causes* trust) is made."),
])

write("analysis/fraud_pattern_analysis.ipynb", [
    md("# Fraud pattern analysis\nWhich *types* of fraud does the champion model catch? Patterns (`account_takeover`, `card_testing`, `synthetic_identity`, `social_engineering`) exist only as analysis labels - never as features."),
    code("fe = load_features(); summ = load_summary(); champ = summ['models']['champion']; model = load_model(champ)\nfrom src.feature_engineering.features import feature_names\nthr = summ['models']['results'][champ]['threshold']\nte = fe[fe.split=='test'].copy(); te['score'] = model.predict_proba(te[feature_names()])[:,1]; te['pred'] = te.score >= thr\nprint('champion:', champ, '| threshold', round(thr, 3))"),
    code("f = te[te.is_fraud==1]\nf.groupby('fraud_pattern').agg(frauds=('pred','size'), detected=('pred','mean'), mean_amount=('amount','mean')).round(3)"),
    code("sig = fe[fe.is_fraud==1].groupby('fraud_pattern')[['is_new_device','is_foreign','ip_risk_score','velocity_1h','log_amount','amount_to_cust_avg_ratio','is_night','is_new_account']].mean()\nlegit = fe[fe.is_fraud==0][sig.columns].mean(); sig.loc['(legit baseline)'] = legit\nsns.heatmap(sig.round(2), annot=True, cmap='rocket_r', fmt='.2f'); plt.title('Feature signature per fraud pattern')"),
    code("missed = f[~f.pred]; print('missed frauds:', len(missed), '| value missed:', round(missed.amount.sum(), 1)); missed.fraud_pattern.value_counts()"),
    md("Social-engineering fraud (legitimate device and geography, customer authenticates with OTP) is the hardest class: its behavioural footprint resembles legitimate high-value transfers. This motivates behavioural/biometric signals and consumer education as complements to ML (see Chapter 6)."),
])

write("analysis/statistical_analysis.ipynb", [
    md("# Statistical analysis\nFormal tests supporting the research questions. Significance level α = 0.05 with Bonferroni correction across the family of tests."),
    code("from src.model_evaluation import statistics as st\nfrom src.model_evaluation.evaluate import bootstrap_ci\ndf = load_clean(); fe = load_features(); summ = load_summary()"),
    code("# H1: fraud amounts differ from legitimate amounts (non-parametric)\nh1 = st.mann_whitney(df[df.is_fraud==1].amount, df[df.is_fraud==0].amount); h1"),
    code("# H2: channel and fraud are associated\nh2 = st.chi_square(df, 'channel', 'is_fraud'); h2"),
    code("# H3: authentication method and fraud are associated\nh3 = st.chi_square(df, 'auth_method', 'is_fraud'); h3"),
    code("sv = load_survey(); sc = load_trust(); full = sv.merge(sc[['respondent_id','trust_score']], on='respondent_id')\nh4 = st.kruskal(full, 'trust_score', 'age_band'); h5 = st.mann_whitney(full[full.experienced_fraud==1].trust_score, full[full.experienced_fraud==0].trust_score)\nh4, h5"),
    code("tests = {'H1 amount': h1['p_value'], 'H2 channel': h2['p_value'], 'H3 auth': h3['p_value'], 'H4 age trust': h4['p_value'], 'H5 fraud-experience trust': h5['p_value']}\nm = len(tests)\npd.DataFrame({'p': tests, 'bonferroni_p': {k: min(v*m, 1) for k, v in tests.items()}, 'significant@0.05': {k: v*m < .05 for k, v in tests.items()}})"),
    code("# Model comparison: McNemar (paired errors) and bootstrap CI for the champion\nprint('McNemar champion vs LR:', summ['models']['mcnemar_vs_lr'])\nprint('Champion ROC-AUC 95% CI:', summ['models']['champion_roc_auc_ci95'])"),
    md("Effect sizes (Cramér's V, rank-biserial) are reported alongside p-values: with tens of thousands of rows, tiny effects become 'significant', so magnitude matters."),
])

# =============================== notebooks/ ===================================================
write("notebooks/01_data_preprocessing.ipynb", [
    md("# 01 - Data preprocessing\nGenerate (or load) data → validate → clean → store as Parquet/CSV. Reproducible via seed in `config/settings.yaml`."),
    code("from src.data_collection.synthetic import generate_transactions\nfrom src.preprocessing.validation import validate_transactions\nfrom src.preprocessing.cleaning import clean_transactions, frame_hash\ns = CFG['synthetic']\nraw = generate_transactions(20000, s['n_customers'], s['fraud_rate'], 60, CFG['seed'], '2025-06-30', s['dirty_fraction'])\nprint(raw.shape)"),
    code("pd.DataFrame(validate_transactions(raw, CFG))[['check','passed','failed_count']]"),
    code("clean, rep = clean_transactions(raw); print(rep)\nprint('content hash (same seed -> same hash):', frame_hash(clean.drop(columns=['timestamp'])))"),
    code("again, _ = clean_transactions(generate_transactions(20000, s['n_customers'], s['fraud_rate'], 60, CFG['seed'], '2025-06-30', s['dirty_fraction']))\nassert frame_hash(again.drop(columns=['timestamp'])) == frame_hash(clean.drop(columns=['timestamp'])); print('reproducible: OK')"),
    code("import tempfile, os\nwith tempfile.TemporaryDirectory() as d:\n    clean.to_parquet(f'{d}/t.parquet', index=False); clean.to_csv(f'{d}/t.csv', index=False)\n    print({f: os.path.getsize(f'{d}/{f}')//1024 for f in os.listdir(d)}, 'KiB')"),
    md("Parquet keeps dtypes and is several times smaller than CSV; the pipeline stores both (CSV for portability, Parquet for speed)."),
])

write("notebooks/02_feature_engineering.ipynb", [
    md("# 02 - Feature engineering\nLeakage-safe features: customer-history aggregates use **only earlier** rows."),
    code("from src.feature_engineering.features import build_features, feature_names, NUMERIC_FEATURES\nclean = load_clean(); X = build_features(clean); X.shape"),
    code("pd.DataFrame({'feature': NUMERIC_FEATURES}).assign(group=lambda d: np.where(d.feature.str.contains('_x_'), 'interaction', np.where(d.feature.str.contains('cust|ratio|secs'), 'customer history', 'transaction')))"),
    code("# leakage test: altering the LAST transaction must not alter any earlier feature row\nmod = clean.copy(); mod.loc[mod.index[-1], 'amount'] = 1e6\npd.testing.assert_frame_equal(build_features(mod).iloc[:-1], X.iloc[:-1]); print('no future leakage: OK')"),
    code("from sklearn.feature_selection import mutual_info_classif\nmi = pd.Series(mutual_info_classif(X.iloc[:20000], clean.is_fraud.iloc[:20000], random_state=0), index=X.columns).sort_values()\nmi.tail(15).plot.barh(figsize=(7, 5), title='Mutual information with fraud label')"),
    code("corr = X[NUMERIC_FEATURES].corr(method='spearman'); sns.clustermap(corr, cmap='vlag', center=0, figsize=(9, 9))"),
    md("Highly correlated pairs (e.g. `is_new_device` and `new_device_x_foreign`) are tolerated: tree models are robust and Logistic Regression is L2-regularised."),
])

write("notebooks/03_fraud_detection.ipynb", [
    md("# 03 - Supervised fraud detection\nLogistic Regression, Random Forest and XGBoost on a **chronological** split (train 70% / validation 15% / test 15%)."),
    code("from src.fraud_detection.train import train_and_select, evaluate_models\nfrom src.model_evaluation.evaluate import comparison_table\nimport copy\nfe = load_features(); d = split_xy(fe)\nX_tr, y_tr, _ = d['train']; X_va, y_va, _ = d['validation']; X_te, y_te, te = d['test']\nprint({k: (len(v[1]), int(v[1].sum())) for k, v in d.items()}, '(rows, frauds)')"),
    code("cfg = copy.deepcopy(CFG); cfg['tuning']['n_iter'] = 3   # quick demo; the pipeline uses the value in settings.yaml\ntrained = train_and_select(X_tr, y_tr, X_va, y_va, cfg)\nresults, scores = evaluate_models(trained, X_te, y_te)\ncomparison_table(results).round(4)"),
    code("pd.DataFrame({k: v['params'] for k, v in trained.items()}).T"),
    code("from sklearn.metrics import PrecisionRecallDisplay, RocCurveDisplay\nfig, ax = plt.subplots(1, 2, figsize=(13, 4.5))\nfor k, s in scores.items():\n    RocCurveDisplay.from_predictions(y_te, s, name=k, ax=ax[0]); PrecisionRecallDisplay.from_predictions(y_te, s, name=k, ax=ax[1])\nax[0].set_title('ROC'); ax[1].set_title('Precision-Recall')"),
    code("print('Pipeline (full-tuning) results for comparison:')\ncomparison_table({k: v for k, v in load_summary()['models']['results'].items() if k in trained}).round(4)"),
    md("Class imbalance (~2%) is handled by `class_weight` / `scale_pos_weight`; thresholds are tuned on the **validation** set so the test set remains untouched."),
])

write("notebooks/04_anomaly_detection.ipynb", [
    md("# 04 - Unsupervised anomaly detection\nIsolation Forest and Local Outlier Factor trained **without labels**. Useful when fraud labels are delayed or novel attacks appear."),
    code("from src.anomaly_detection.detectors import fit_isolation_forest, iso_scores, fit_lof, lof_scores\nfrom sklearn.metrics import roc_auc_score, average_precision_score\nfe = load_features(); d = split_xy(fe); X_tr, y_tr, _ = d['train']; X_te, y_te, _ = d['test']"),
    code("iso = fit_isolation_forest(X_tr, 0.02, CFG['seed']); si = iso_scores(iso, X_te)\nlof = fit_lof(X_tr, 6000, 35, 0.02, CFG['seed']); sl = lof_scores(lof, X_te)\npd.DataFrame({'ROC-AUC': {'isolation_forest': roc_auc_score(y_te, si), 'lof': roc_auc_score(y_te, sl)}, 'PR-AUC': {'isolation_forest': average_precision_score(y_te, si), 'lof': average_precision_score(y_te, sl)}}).round(3)"),
    code("# Precision when we review only the top-k most anomalous transactions\nrows = []\nfor k in (50, 100, 200, 500):\n    for name, s in (('iso', si), ('lof', sl)):\n        top = np.argsort(-s)[:k]; rows.append({'k': k, 'detector': name, 'precision@k': y_te[top].mean(), 'recall@k': y_te[top].sum() / y_te.sum()})\npd.DataFrame(rows).pivot(index='k', columns='detector').round(3)"),
    code("# sensitivity to contamination\nfrom src.model_evaluation.evaluate import evaluate_binary\nout = []\nfor c in (0.005, 0.01, 0.02, 0.05, 0.1):\n    thr = np.quantile(si, 1-c); r = evaluate_binary(y_te, si, thr); out.append({'contamination': c, 'precision': r['precision'], 'recall': r['recall'], 'f1': r['f1'], 'FPR': r['false_positive_rate']})\npd.DataFrame(out).round(3)"),
    code("sns.kdeplot(x=si, hue=y_te, common_norm=False); plt.title('Isolation Forest score: legit (0) vs fraud (1)')"),
    md("Unsupervised scores rank fraud far above chance but trail supervised models - the price of not using labels. Combining both (score as an extra feature) is listed under Future Work."),
])

write("notebooks/05_consumer_trust_scoring.ipynb", [
    md("# 05 - Consumer Trust scoring\nCTS (survey) + Platform Security Index (measured) → Consumer Trust Index. Includes a **sensitivity analysis** because the weights are a design choice, not a measured constant."),
    code("from src.trust_scoring.scoring import *\nsv = load_survey(); sc = score_respondents(sv, CFG); summ = load_summary()\nprint(CFG['trust']['weights'])\nsc.trust_score.describe().round(1)"),
    code("m = summ['models']['results'][summ['models']['champion']]\npsi = platform_security_index(m['recall'], m['false_positive_rate'], summ['security']['attack_block_rate'], summ['validation']['pass_rate'])\ncti = consumer_trust_index(sc.trust_score.mean(), psi, CFG['trust']['survey_weight_in_index'])\nprint(f'PSI={psi:.1f}  mean CTS={sc.trust_score.mean():.1f}  CTI={cti:.1f}')"),
    code("# sensitivity 1: weight on the survey component\ngrid = pd.DataFrame({'survey_weight': np.linspace(0, 1, 11)}); grid['CTI'] = [consumer_trust_index(sc.trust_score.mean(), psi, a) for a in grid.survey_weight]\ngrid.plot(x='survey_weight', y='CTI', marker='o', title='CTI vs survey weight')"),
    code("# sensitivity 2: random dimension weights (Dirichlet) -> how stable is the respondent ranking?\nfrom scipy.stats import spearmanr\ndims = dimension_scores(sv); base = sc.trust_score\nrng = np.random.default_rng(0); rhos = []\nfor _ in range(500):\n    w = rng.dirichlet(np.ones(5)); rhos.append(spearmanr(base, dims.to_numpy() @ w).statistic)\nprint(f'Rank correlation with default weights: median {np.median(rhos):.3f}, 5th pct {np.percentile(rhos, 5):.3f}')"),
    code("print({k: round(v, 3) for k, v in reliability_report(sv).items()})"),
    md("Rankings are robust to weighting (rho close to 1) while the *level* of CTI depends on the chosen survey weight - report both. CTI is a proposed composite, not a validated instrument."),
])

write("notebooks/06_model_training.ipynb", [
    md("# 06 - Model training & hyper-parameter tuning\nDetailed look at randomised search for XGBoost, plus serialisation and metadata (what the pipeline does in its `train` and `persist` stages)."),
    code("from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold\nfrom src.fraud_detection.train import candidate_models\nfe = load_features(); d = split_xy(fe); X_tr, y_tr, _ = d['train']; X_va, y_va, _ = d['validation']\npw = (y_tr == 0).sum() / (y_tr == 1).sum(); est, space = candidate_models(CFG['seed'], pw, 2)['xgboost']"),
    code("search = RandomizedSearchCV(est, space, n_iter=12, scoring='average_precision', cv=StratifiedKFold(3, shuffle=True, random_state=CFG['seed']), random_state=CFG['seed'], n_jobs=1, return_train_score=True).fit(X_tr, y_tr)\nres = pd.DataFrame(search.cv_results_)[['mean_train_score','mean_test_score','std_test_score','param_max_depth','param_learning_rate','param_subsample']].sort_values('mean_test_score', ascending=False); res.round(4).head(8)"),
    code("res.plot.scatter(x='mean_train_score', y='mean_test_score', title='Train vs CV score (overfitting check)'); plt.plot([0.3, 1], [0.3, 1], 'k--', lw=.8)"),
    code("import joblib, json, tempfile, pathlib\nbest = search.best_estimator_; print(search.best_params_)\nwith tempfile.TemporaryDirectory() as t:\n    p = pathlib.Path(t) / 'xgb.joblib'; joblib.dump(best, p); back = joblib.load(p)\n    assert np.allclose(back.predict_proba(X_va)[:, 1], best.predict_proba(X_va)[:, 1]); print('serialisation round-trip OK,', p.stat().st_size // 1024, 'KiB')"),
    code("print(json.dumps(json.loads((ROOT / 'models' / 'model_metadata' / 'xgboost.json').read_text()), indent=1)[:1500])"),
    md("Search scoring uses **average precision** (area under PR curve) rather than accuracy, as it reflects performance on the rare positive class."),
])

write("notebooks/07_model_evaluation.ipynb", [
    md("# 07 - Model evaluation\nReloads the **serialised** models and evaluates on the untouched test partition: accuracy, precision, recall, F1, ROC-AUC, PR-AUC, confusion matrices, false-positive rate, threshold trade-offs, calibration and risk tiers."),
    code("from src.model_evaluation.evaluate import evaluate_binary, comparison_table, bootstrap_ci\nfrom src.fraud_detection.risk import tier_summary\nsumm = load_summary(); fe = load_features(); d = split_xy(fe); X_te, y_te, te = d['test']\nnames = ['logistic_regression', 'random_forest', 'xgboost']\nmodels = {n: load_model(n) for n in names}; scores = {n: m.predict_proba(X_te)[:, 1] for n, m in models.items()}\nres = {n: evaluate_binary(y_te, scores[n], summ['models']['results'][n]['threshold']) for n in names}\ncomparison_table(res).round(4)"),
    code("ci = {n: bootstrap_ci(y_te, scores[n], n_boot=200) for n in names}; pd.DataFrame(ci, index=['ROC-AUC 2.5%', 'ROC-AUC 97.5%']).T.round(4)"),
    code("fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))\nfor a, n in zip(ax, names):\n    r = res[n]; sns.heatmap([[r['tn'], r['fp']], [r['fn'], r['tp']]], annot=True, fmt='d', cmap='Blues', cbar=False, ax=a, xticklabels=['Legit', 'Fraud'], yticklabels=['Legit', 'Fraud']); a.set_title(f\"{n}\\nFPR {r['false_positive_rate']:.3%}\")\nplt.tight_layout()"),
    code("# threshold trade-off for the champion\nch = summ['models']['champion']; rows = [dict(threshold=t, **{k: v for k, v in evaluate_binary(y_te, scores[ch], t).items() if k in ('precision', 'recall', 'f1', 'false_positive_rate')}) for t in np.linspace(0.02, 0.98, 25)]\npd.DataFrame(rows).set_index('threshold')[['precision', 'recall', 'f1', 'false_positive_rate']].plot(figsize=(8, 4), title=f'Threshold sweep - {ch}')"),
    code("from sklearn.calibration import calibration_curve\nfig, ax = plt.subplots(figsize=(5, 5))\nfor n in names:\n    fp_, mp_ = calibration_curve(y_te, scores[n], n_bins=8, strategy='quantile'); ax.plot(mp_, fp_, marker='o', label=n)\nax.plot([0, 1], [0, 1], 'k--'); ax.set(xlabel='mean predicted probability', ylabel='observed fraud rate', title='Calibration'); ax.legend()"),
    code("tier_summary(scores[ch], y_te, te.amount.to_numpy(), CFG['risk_tiers']).round(4)"),
    code("# business view: money saved vs friction (flagged legit transactions)\nthr = summ['models']['results'][ch]['threshold']; pred = scores[ch] >= thr; amt = te.amount.to_numpy()\nprint(f'fraud value caught: {amt[pred & (y_te==1)].sum():,.0f} | missed: {amt[~pred & (y_te==1)].sum():,.0f} | legit customers flagged: {int((pred & (y_te==0)).sum())} of {int((y_te==0).sum())}')"),
    md("**Reading the false-positive rate:** even FPR ≈ 0.5% means thousands of wrongly challenged customers at scale - a direct link between model quality and consumer trust."),
])

write("notebooks/08_research_visualization.ipynb", [
    md("# 08 - Research visualisation\nPublication-quality figures exported to `report/figures/` and interactive Plotly views."),
    code("summ = load_summary(); res = pd.DataFrame(summ['models']['results']).T.reset_index(names='model')\nfig = px.bar(res.melt('model', ['precision', 'recall', 'f1', 'roc_auc', 'pr_auc'], 'metric', 'value'), x='model', y='value', color='metric', barmode='group', title='Model comparison (test set)'); fig"),
    code("tx = summ['transactions']; hr = pd.Series(tx['fraud_rate_by_hour']).rename_axis('hour').reset_index(name='rate')\npx.bar(hr, x='hour', y='rate', title='Fraud rate by hour of day')"),
    code("ev = load_events(); ev['timestamp'] = pd.to_datetime(ev.timestamp)\npx.histogram(ev[ev.is_attack == 1], x='timestamp', color='event_type', nbins=90, title='Attack events over time (campaign bursts)')"),
    code("sc = load_trust(); sv = load_survey()\nfull = sv.merge(sc[['respondent_id', 'trust_score']], on='respondent_id')\npx.box(full, x='age_band', y='trust_score', color='experienced_fraud', category_orders={'age_band': ['18-24', '25-34', '35-44', '45-54', '55+']}, title='Trust by age band and past fraud experience')"),
    code("fig, ax = plt.subplots(figsize=(7, 4.5)); sns.scatterplot(data=full, x='digital_literacy', y='trust_score', hue='uses_mfa', alpha=.6, ax=ax)\nfig.savefig(ROOT / 'report' / 'figures' / 'trust_vs_literacy.png', dpi=140, bbox_inches='tight')"),
    code("import os; print(sorted(os.listdir(ROOT / 'report' / 'figures')))"),
])

# =============================== survey/ =========================================================
write("survey/survey_analysis.ipynb", [
    md("# Survey analysis - consumer perceptions of FinTech cybersecurity and trust\nInstrument: `questionnaire.md` (12 five-point Likert items, 3 demographic bands, 3 behaviours). **Privacy:** pseudonymised ID, banded demographics, k-anonymity enforced, no free text.\n\n> The bundled CSV is synthetic (latent-factor model). Replace `survey_data.csv` with real, consented responses and re-run."),
    code("from src.preprocessing.anonymize import k_anonymity\nfrom src.trust_scoring.scoring import score_respondents, reliability_report, reverse_code\nfrom src.schema import SURVEY_ITEMS\nsv = load_survey(); print(sv.shape); k_anonymity(sv, CFG['trust']['k_anonymity'])"),
    code("items = list(SURVEY_ITEMS)\ndesc = sv[items].agg(['mean', 'std', 'median']).T; desc['dimension'] = [SURVEY_ITEMS[q][0] for q in items]; desc['text'] = [SURVEY_ITEMS[q][1][:70] for q in items]; desc.round(2)"),
    code("lik = sv[items].apply(lambda c: c.value_counts(normalize=True)).T.fillna(0).sort_index(axis=1)\nlik.plot.barh(stacked=True, colormap='RdYlGn', figsize=(10, 5), title='Likert response distribution'); plt.legend(title='1=strongly disagree ... 5=strongly agree', bbox_to_anchor=(1, 1))"),
    code("r = reverse_code(sv); sns.heatmap(r[items].corr(method='spearman'), cmap='vlag', center=0, annot=True, fmt='.2f', annot_kws={'size': 7}); plt.title('Inter-item Spearman correlation (q12 reverse-coded)')"),
    code("sc = score_respondents(sv, CFG); full = sv.merge(sc[['respondent_id', 'trust_score', 'segment']], on='respondent_id')\nfull.groupby('uses_mfa').trust_score.agg(['count', 'mean', 'std']).round(1).join(full.groupby('experienced_fraud').trust_score.mean().round(1).rename('by_fraud_exp'), how='outer')"),
    code("pd.crosstab(full.usage_frequency, full.segment, normalize='index').round(3)"),
    code("pd.Series(reliability_report(sv)).round(3).to_frame('Cronbach alpha')"),
])
print("done")
