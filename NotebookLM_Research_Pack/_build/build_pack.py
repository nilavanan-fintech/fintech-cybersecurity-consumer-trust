"""Build the NotebookLM Research Knowledge Pack (read-only on the project; writes only inside NotebookLM_Research_Pack/).

    python NotebookLM_Research_Pack/_build/build_pack.py
Requires reportlab, pillow, pyyaml, python-pptx. Does not need pandas.
"""
import datetime
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import facts as F  # noqa: E402
import docs_a, docs_b  # noqa: E402

OUT = ROOT / "NotebookLM_Research_Pack"

DOCS = [
    ("01_Project_Overview.pdf", docs_a.d01, "What the project is, components, verification state, repository map"),
    ("02_Problem_Statement_and_Objectives.pdf", docs_a.d02, "Problem, aim, objectives O1-O6, research questions RQ1-RQ7, ethics scope"),
    ("03_Literature_Review_and_Research_Gap.pdf", docs_a.d03, "Only the works in references.bib, themes, research gap and its status"),
    ("04_Research_Methodology.pdf", docs_a.d04, "Pipeline stages, split/tuning protocol, metrics explained, trust methodology, validity threats"),
    ("05_System_Architecture_and_Technology_Stack.pdf", docs_a.d05, "Docker services parsed from compose, diagrams, data flow, technologies"),
    ("06_Dataset_and_Data_Preprocessing.pdf", docs_a.d06, "Datasets, fraud patterns, validation checks, cleaning, features, survey privacy"),
    ("07_Machine_Learning_and_Fraud_Detection.pdf", docs_b.d07, "Algorithms, training, thresholds, risk tiers, real results if a run exists"),
    ("08_Consumer_Trust_Analytics.pdf", docs_b.d08, "Survey instrument, CTS/PSI/CTI, statistics, privacy, gaps"),
    ("09_Docker_Prometheus_and_Grafana.pdf", docs_b.d09, "Containers, Prometheus metrics (parsed), alerts, Loki, 7 dashboards, PostgreSQL design"),
    ("10_Implementation_and_Code_Explanation.pdf", docs_b.d10, "Every module and public function (parsed), tests, notebooks, incomplete items"),
    ("11_Monthly_Project_Reviews.pdf", docs_b.d11, "Review 1 to Review 4 slide content read from the pptx files, chronologically"),
    ("12_Experimental_Results_and_Conclusion.pdf", docs_b.d12, "Pipeline-produced results, guardrails, conclusions, limitations, future work"),
    ("13_Final_Year_Viva_Preparation.pdf", docs_b.d13, "20 grounded viva questions with answers, honesty checklist, demo plan"),
]


def readme(built):
    rows = "\n".join(f"| {i} | `{n}` | {desc} |" for i, (n, _, desc) in enumerate(DOCS, 1))
    return f"""# NotebookLM Research Knowledge Pack - FinTech Cybersecurity and Consumer Trust

Generated {datetime.date.today().isoformat()} from the project files (read-only). Contains 13 PDFs, a podcast prompt and a validation report.
Nothing in the pack is invented: facts come from source code, notebooks, configs, review decks and pipeline output; missing or unverified items are labelled.

## Upload order

| # | File | Contents |
|---|---|---|
{rows}

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
"""


PROMPT = """TANGLISH PODCAST PROMPT - FinTech Cybersecurity and Consumer Trust

=== SHORT VERSION (paste into NotebookLM Audio Overview > Customize if there is a length limit) ===
Make a 30-40 minute conversational educational podcast with two speakers: RAVI, a technical researcher who built this final-year project, and KAVI, a curious Tamil engineering student. Speak in natural Tanglish: Tamil written in English letters mixed with English technical terms (for example "idhu epdi work aagudhu", "false positive-nu sollrom", "model train pannum bodhu"). Keep technical words (precision, recall, PR-AUC, Docker, Prometheus, Grafana, PostgreSQL) in English. Cover, in order: introduction and problem, literature review and research gap, methodology, datasets and preprocessing, fraud detection, anomaly detection, consumer trust scoring, ML evaluation, PostgreSQL, Docker, Prometheus, Grafana, the four monthly reviews, experimental results, limitations, conclusion, and viva preparation. Use ONLY facts from the uploaded sources. Say clearly that the data and the survey are synthetic. Never invent numbers, papers, features or results; if a source does not say it, say "idhu sources-la illa". Use simple money examples (UPI payments, card swipes, a salary account) and clearly mark them as illustrative examples, not project results.

=== FULL INSTRUCTIONS ===

1. FORMAT
- Length: 30-40 minutes (about 4,500-6,000 spoken words).
- Two speakers, alternating naturally, with short reactions ("ohh", "sari", "puriyudhu", "wait wait, konjam explain pannunga").
- RAVI = technical researcher (calm, precise, uses analogies). KAVI = curious Tamil engineering student (asks "why", repeats ideas in own words, sometimes confused, sometimes funny).
- Begin with a 1-minute hook, end with a 3-minute recap and viva tips.

2. LANGUAGE STYLE (TANGLISH)
- Sentence structure in Tamil written in English letters; technical terms in English. Example: "Fraud detection-la main problem enna-na, fraud romba rare. 100 transactions-la 2 dhaan fraud irukkum, so accuracy-a mattum paartha misleading."
- Keep it respectful and friendly: "nga", "paa", "da" used lightly. No Tamil script, no heavy literary Tamil.
- Define every technical term the first time, in one simple Tanglish sentence, then use the English term.
- Avoid long English paragraphs; avoid unexplained jargon.

3. TRUTHFULNESS RULES (VERY IMPORTANT)
- Use only information from the uploaded PDFs. Do not add outside papers, datasets, numbers or features.
- The transactions, security events and survey are SYNTHETIC (generated with a fixed seed). Say this at least three times: early, when discussing results, and in the conclusion.
- Quote numeric results only if they appear in document 07 or 12; mention that they come from one seed, a small tuning budget and few fraud cases in the test set.
- Distinguish IMPLEMENTED vs PLANNED vs MISSING (document 01 verification table, documents 07, 08, 10). Missing items include: real survey data, ethics approval, Grafana screenshots, public-dataset results, psychometric validation of the Trust Index. Say so honestly.
- Illustrative examples (UPI, card swipe) must be labelled "example", never "project result".
- If asked something the sources do not cover, say so and suggest checking the project files.

4. EPISODE OUTLINE (with approximate timing)
 A. Intro and hook (0:00-2:30): why FinTech security and customer trust matter; UPI/card example of "app secure irundhaalum customer-ku trust illa".
 B. Problem statement and objectives O1-O6, research questions (2:30-6:00) - doc 02.
 C. Literature review and research gap (6:00-10:00) - doc 03: only works listed in the references; explain each theme (fraud ML, imbalance and PR curves, anomaly detection, trust models, Cronbach alpha, k-anonymity) in simple words; the gap.
 D. Methodology (10:00-14:00) - doc 04: pipeline stages, chronological split (explain "future-la irundhu learn pannakoodadhu"), tuning, threshold on validation, metrics.
 E. Datasets and preprocessing (14:00-18:00) - doc 06: synthetic generators, four fraud patterns, injected dirty data, 13 validation checks, cleaning, feature engineering and leakage prevention, survey privacy.
 F. Fraud detection and anomaly detection (18:00-24:00) - doc 07: Logistic Regression, Random Forest, XGBoost, Isolation Forest, LOF in simple language; class imbalance; risk tiers; false-positive rate and customer friction with a money example.
 G. Consumer trust scoring (24:00-27:00) - doc 08: Likert items, dimensions, reverse coding, CTS, PSI, CTI, Cronbach alpha; stress that the index is a proposal and the survey is synthetic.
 H. PostgreSQL, Docker, Prometheus, Grafana, Loki (27:00-33:00) - doc 09: what each does, how docker compose up works, metrics from the worker, live replay of held-out data, 7 dashboards, alerts.
 I. The four monthly reviews (33:00-36:00) - doc 11: what Review 1, 2, 3, 4 covered and how the project progressed.
 J. Results, limitations, conclusion (36:00-38:00) - doc 12.
 K. Viva preparation and recap (38:00-40:00) - doc 13: 5 likely questions with short Tanglish answers, the honesty checklist, demo order.

5. TEACHING TECHNIQUES
- KAVI should misunderstand at least four things and RAVI corrects them (for example: "accuracy 98%-na model super-a?" -> no, because of imbalance).
- Use analogies: Isolation Forest = "oru crowd-la odd person-a seekiram identify pannuradhu"; chronological split = "exam-la next year paper-a munnadiye paakkama irukkanum".
- Recap every 8-10 minutes in two sentences.

6. THINGS TO AVOID
- No invented statistics, citations, benchmarks, company names or claims that the system is deployed in production.
- No claim that the project proves consumer behaviour in the real world.
- No reading of code line by line; explain ideas.

7. CLOSING
End with: what is implemented, what is still planned or missing, and three practical viva tips (know the limitations, quote numbers with context, demo the dashboards in a fixed order).
"""


def validation(built, errors):
    s = F.summary()
    lines = ["# Validation report", "", f"Generated {datetime.datetime.now():%Y-%m-%d %H:%M}.", "", "## Generated files", "", "| File | Size (KB) | Pages |", "|---|---|---|"]
    try:
        from pypdf import PdfReader  # optional
    except Exception:
        PdfReader = None
    for n, _, _ in DOCS:
        p = OUT / n
        if p.exists():
            pages = len(PdfReader(str(p)).pages) if PdfReader else "n/a"
            lines.append(f"| {n} | {p.stat().st_size // 1024} | {pages} |")
        else:
            lines.append(f"| {n} | MISSING | - |")
    for n in ("README.md", "TANGLISH_PODCAST_PROMPT.txt", "VALIDATION_REPORT.md"):
        lines.append(f"| {n} | {'ok' if (OUT / n).exists() or n == 'VALIDATION_REPORT.md' else 'MISSING'} | - |")
    lines += ["", "## Source coverage", "", f"- Python modules parsed: {len(F.modules())}", f"- Notebooks found: {len(F.notebooks())} (with stored outputs: {sum(1 for n in F.notebooks() if n['with_output'])})",
              f"- Dashboards parsed: {len(F.dashboards())}", f"- Prometheus metrics parsed: {len(F.metrics())}", f"- SQL tables parsed: {len(F.sql_tables())}", f"- Review decks read: {len(F.reviews())} of 4",
              f"- Pipeline run summary present: {'yes (run ' + s['run_id'] + ')' if s else 'NO - results sections say so'}", f"- Recorded run status: {F.run_status() or 'none'}"]
    lines += ["", "## Missing or incomplete source information", ""]
    miss = []
    if not s: miss.append("No pipeline run summary - experimental numbers absent.")
    if len(F.reviews()) < 4: miss.append("One or more review decks missing.")
    if not any(n["with_output"] for n in F.notebooks()): miss.append("Notebooks have no stored outputs (generated, not executed).")
    if not list((ROOT / "review" / "assets").glob("*.png")): miss.append("No Grafana screenshots in review/assets.")
    for f in ("report/chapters/chapter_5_results.md", "report/chapters/chapter_6_conclusion.md", "survey/survey_results.md", "report/tables/results_summary.md"):
        if not (ROOT / f).exists(): miss.append(f"{f} does not exist.")
    miss += ["survey_data.csv is synthetic; no real respondents or ethics approval recorded.", "Bibliography entries not verified against publisher records.", "No CI configuration; no automated tests for exporter/worker."]
    lines += [f"- {m}" for m in miss]
    if errors: lines += ["", "## Build errors", ""] + [f"- {e}" for e in errors]
    lines += ["", "## Integrity checks", "", "- Original project files were only read. All outputs are inside NotebookLM_Research_Pack/.", "- Text uses ASCII-safe characters so PDFs are fully text-selectable for NotebookLM."]
    return "\n".join(lines)


def main():
    OUT.mkdir(exist_ok=True)
    built, errors = [], []
    for name, fn, _ in DOCS:
        try:
            p = fn().build(OUT); built.append(name); print("built", p.name)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{name}: {e!r}"); print("FAILED", name, repr(e))
    (OUT / "README.md").write_text(readme(built), encoding="utf-8")
    (OUT / "TANGLISH_PODCAST_PROMPT.txt").write_text(PROMPT, encoding="utf-8")
    (OUT / "VALIDATION_REPORT.md").write_text(validation(built, errors), encoding="utf-8")
    print("done;", len(built), "pdfs;", len(errors), "errors")


if __name__ == "__main__":
    main()
