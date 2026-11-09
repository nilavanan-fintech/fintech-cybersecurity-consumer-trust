# NotebookLM Research Knowledge Pack - FinTech Cybersecurity and Consumer Trust

Generated 2026-11-09 from the project files (read-only). Contains 13 PDFs, a podcast prompt and a validation report.
Nothing in the pack is invented: facts come from source code, notebooks, configs, review decks and pipeline output; missing or unverified items are labelled.

## Upload order

| # | File | Contents |
|---|---|---|
| 1 | `01_Project_Overview.pdf` | What the project is, components, verification state, repository map |
| 2 | `02_Problem_Statement_and_Objectives.pdf` | Problem, aim, objectives O1-O6, research questions RQ1-RQ7, ethics scope |
| 3 | `03_Literature_Review_and_Research_Gap.pdf` | Only the works in references.bib, themes, research gap and its status |
| 4 | `04_Research_Methodology.pdf` | Pipeline stages, split/tuning protocol, metrics explained, trust methodology, validity threats |
| 5 | `05_System_Architecture_and_Technology_Stack.pdf` | Docker services parsed from compose, diagrams, data flow, technologies |
| 6 | `06_Dataset_and_Data_Preprocessing.pdf` | Datasets, fraud patterns, validation checks, cleaning, features, survey privacy |
| 7 | `07_Machine_Learning_and_Fraud_Detection.pdf` | Algorithms, training, thresholds, risk tiers, real results if a run exists |
| 8 | `08_Consumer_Trust_Analytics.pdf` | Survey instrument, CTS/PSI/CTI, statistics, privacy, gaps |
| 9 | `09_Docker_Prometheus_and_Grafana.pdf` | Containers, Prometheus metrics (parsed), alerts, Loki, 7 dashboards, PostgreSQL design |
| 10 | `10_Implementation_and_Code_Explanation.pdf` | Every module and public function (parsed), tests, notebooks, incomplete items |
| 11 | `11_Monthly_Project_Reviews.pdf` | Review 1 to Review 4 slide content read from the pptx files, chronologically |
| 12 | `12_Experimental_Results_and_Conclusion.pdf` | Pipeline-produced results, guardrails, conclusions, limitations, future work |
| 13 | `13_Final_Year_Viva_Preparation.pdf` | 20 grounded viva questions with answers, honesty checklist, demo plan |

Then add `TANGLISH_PODCAST_PROMPT.txt` (see below). `VALIDATION_REPORT.md` and this README are for you; they need not be uploaded.

## Importing into NotebookLM (manual)
1. Open your NotebookLM notebook in the browser (the link you gave: https://notebook.google.com/notebook/0f3b3dfe-d1ef-42f0-ada8-5d7824fe207c). This pack was generated offline; nothing was uploaded for you.
2. Click **Add source** -> **Upload file** and select the 13 PDFs (you can multi-select; add them in numeric order so citations read chronologically). NotebookLM allows many sources per notebook; each PDF is well below typical size limits.
3. Optionally upload `TANGLISH_PODCAST_PROMPT.txt` as a source, **or** paste its contents into **Audio Overview -> Customize** (the "what should the AI hosts focus on" box). If the box has a character limit, paste the section "SHORT VERSION" at the top of the file and keep the full text as a source.
4. Generate the Audio Overview. Note: NotebookLM's audio language support and its adherence to customisation instructions vary; Tanglish (Tamil in English letters mixed with English) may come out as plain English or another style. If so, use the same prompt in the chat panel to get a Tanglish *script* and read it yourself.
5. After the pipeline is re-run or Grafana screenshots are added, rebuild the pack with `python NotebookLM_Research_Pack/_build/build_pack.py` and replace the sources.

## Reading guide
- New to the project: 01 -> 02 -> 04 -> 05 -> 12.
- Technical deep dive: 06 -> 07 -> 08 -> 09 -> 10.
- Viva practice: 11 -> 13.

## Honesty rules used throughout
- Status words: IMPLEMENTED (code exists), VERIFIED (run/checked), PARTIAL, PLANNED, MISSING, NOT VERIFIED, PENDING.
- Results appear only if `models/model_metadata/last_run_summary.json` exists; otherwise the documents say so.
- The survey, transactions and security events are synthetic. No ethics approval, real respondents, public-dataset results or Grafana screenshots exist unless stated.

## Folder contents
`_build/` holds the generator scripts (do not upload). Source project files are unchanged.
