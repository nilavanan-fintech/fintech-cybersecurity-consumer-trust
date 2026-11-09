# Dataset description

## 1. Synthetic transactions (`transactions_synthetic`)
| Column | Type | Meaning |
|---|---|---|
| transaction_id, customer_id | str | surrogate keys (no real identifiers) |
| timestamp | datetime | 90-day window, diurnal pattern with evening peak |
| amount | float | log-normal around a per-customer level (normalised currency units) |
| merchant_category | cat (11) | groceries … cash_withdrawal |
| channel / device_type | cat | mobile_app, web, pos, atm / android, ios, desktop, terminals |
| country / home_country | cat | transaction country vs customer's home country |
| is_new_device | 0/1 | first-seen device |
| ip_risk_score | 0-1 | simulated IP reputation (higher = riskier) |
| velocity_1h | int | transactions by the customer in the last hour (simulated) |
| account_age_days | int | customer tenure |
| auth_method | cat | password, otp, biometric, none |
| **is_fraud** | 0/1 | label (≈2 %, higher for young accounts / digital channels) |
| fraud_pattern | cat | generator pattern - **analysis only, never a feature** |

Fraud patterns: *account_takeover* (new device, foreign, high IP risk, large amount, night), *card_testing* (tiny amounts, high velocity, web),
*synthetic_identity* (very new account, large amount, new device), *social_engineering* (legitimate device/geo, large OTP-authorised transfer).
Each pattern's signature is expressed in 75 % of its cases. Defects injected (≈0.4 %): missing/negative amounts, duplicate rows.

## 2. Synthetic security events (`security_events_synthetic`)
event_id, timestamp, event_type (3 benign + 7 attack types), severity, source_country, target_service, blocked, response_time_s,
bytes_out, failed_attempts, **is_attack**. 18 % attacks; 60 % of them fall inside six campaign windows (3-10 h bursts).

## 3. Survey (`survey/survey_data.csv`)
respondent_id (12-char salted SHA-256 pseudonym), q01-q12 (Likert 1-5), age_band, education, usage_frequency, uses_mfa,
experienced_fraud, digital_literacy (1-5). **Synthetic** latent-factor sample (n≈400) so the pipeline runs end-to-end; replace with real responses.

## 4. Public benchmark (optional)
ULB/Worldline *Credit Card Fraud Detection* (284,807 transactions, 492 frauds, PCA-anonymised V1-V28) - see `data/README.md`.

## 5. Derived datasets
`data/interim/transactions_clean.*`; `data/processed/transactions_features.parquet` (40 model features + labels + `split`),
`security_events_scored.parquet`, `trust_scores.parquet`.

## 6. Quality controls
Validation suite (schema, ranges, domains, duplicates, missingness thresholds), cleaning report, data hash stored in model metadata.
