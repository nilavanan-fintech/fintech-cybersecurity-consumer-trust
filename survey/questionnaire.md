# Consumer perceptions of FinTech cybersecurity and trust - questionnaire

**Purpose.** Measure how consumers perceive the security, privacy and reliability of the FinTech service they use most, and how much they trust it.
**Duration.** ≈ 4 minutes. **Format.** Online form, anonymous.

## Consent and privacy notice (show first)
> This academic survey studies trust in FinTech services. Participation is voluntary and you may stop at any time. We do **not** collect your name,
> e-mail, phone number, IP address, account details, or any free-text answers. Age is recorded in bands only. Responses are stored under a
> randomly derived code, analysed only in aggregate, and groups smaller than 5 people are suppressed in published results. Please do not
> enter personal or financial details anywhere in the form. Contact for questions/withdrawal: *[supervisor / researcher e-mail]*.
> ☐ I am 18 or over and consent to take part.

## Section A - About you (banded)
| Variable | Question | Options |
|---|---|---|
| age_band | Your age | 18-24 · 25-34 · 35-44 · 45-54 · 55+ |
| education | Highest education | secondary · undergraduate · postgraduate |
| usage_frequency | How often do you use FinTech apps (payments, wallets, neo-banks)? | daily · weekly · monthly |
| uses_mfa | Do you use multi-factor authentication on your main FinTech app? | yes (1) / no (0) |
| experienced_fraud | Have you personally been a victim of payment fraud in the last 3 years? | yes (1) / no (0) / prefer not to say (exclude) |
| digital_literacy | I am comfortable managing the security settings of my apps | 1-5 |

## Section B - Trust and security perceptions (1 = strongly disagree … 5 = strongly agree)
| Item | Statement | Dimension |
|---|---|---|
| q01 | I feel my money is safe when I use my main FinTech app. | Perceived security |
| q02 | My FinTech provider uses strong security measures (e.g. MFA, encryption). | Perceived security |
| q03 | I am confident my FinTech provider can detect and stop fraud. | Perceived security |
| q04 | My FinTech provider handles my personal data responsibly. | Privacy assurance |
| q05 | I understand how my financial data is used and shared. | Privacy assurance |
| q06 | My provider clearly communicates security incidents and policy changes. | Transparency |
| q07 | Security and privacy settings are easy to find and understand. | Transparency |
| q08 | The app works reliably when I make payments. | Reliability |
| q09 | My provider resolves fraud or dispute cases quickly and fairly. | Reliability |
| q10 | I would recommend my FinTech provider to friends or family. | Behavioural intent |
| q11 | I intend to keep using FinTech services for my main finances. | Behavioural intent |
| q12 | I worry that my FinTech account could be hacked. **(reverse-coded)** | Perceived security |

## Scoring
Reverse-code q12 (6 − x). Dimension score = mean of its items rescaled `(mean − 1) / 4 × 100`. Consumer Trust Score = weighted mean of the five
dimensions (weights in `config/settings.yaml`). Segments: Low < 50 ≤ Moderate < 75 ≤ High. Reliability: Cronbach's α.

## Data handling checklist
- [x] No direct identifiers, no free text · [x] age banded · [x] respondent ID = salted SHA-256 prefix (`SURVEY_SALT` kept out of git)
- [x] k-anonymity (k = 5) on age_band × education × usage_frequency enforced before analysis (`src/preprocessing/anonymize.py`)
- [ ] Ethics approval / supervisor sign-off recorded (**required before collecting real data**)
- [ ] Pilot with 5-10 people to check wording; compute α on the pilot

## Note on the bundled data
`survey_data.csv` is **synthetic** (latent-factor generator in `src/data_collection/synthetic.py`). It exists to demonstrate the analysis and monitoring pipeline.
Do not report its statistics as findings about real consumers.
