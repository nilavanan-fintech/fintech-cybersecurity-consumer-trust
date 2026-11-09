# Project overview

**Title:** FinTech Cybersecurity and Consumer Trust - a reproducible research & development platform
**Type:** Final-year academic research and development project (Python, no web front end)

## Problem
FinTech services move money through software that attackers target continuously. Providers invest in fraud detection
and threat monitoring, but the *consumer's* trust depends on how safe the service **feels** as well as how safe it
**is**. Few student projects connect the two with measurable, reproducible evidence.

## Aim
Build and evaluate an end-to-end analytical platform that (1) detects fraudulent transactions and anomalous security
events, (2) measures consumer trust from survey data, and (3) monitors the whole experiment operationally.

## Research objectives
1. **O1** - Construct a validated, reproducible pipeline for financial-transaction and security-event data (synthetic + optional public).
2. **O2** - Compare supervised (Logistic Regression, Random Forest, XGBoost) and unsupervised (Isolation Forest, LOF) detectors using imbalance-aware metrics.
3. **O3** - Quantify the operational cost of detection errors (false positives = friction for legitimate customers).
4. **O4** - Measure consumer trust (CTS) with a documented, privacy-conscious survey instrument and analyse its drivers.
5. **O5** - Propose and stress-test a composite Consumer Trust Index combining perceived and measured security.
6. **O6** - Instrument the pipeline so Grafana shows real, continuously-collected experimental data (observability for research).

## Deliverables
Pipeline code (`src/`), 16 notebooks, PostgreSQL results store, Prometheus/Loki/Grafana environment with 7 provisioned
dashboards, tests, Docker Compose deployment, thesis chapters (`report/`), survey instrument.

## Scope and ethics
All attack-related experiments use synthetic telemetry in an isolated container network, or a licensed public dataset.
The survey is voluntary, pseudonymised, banded and k-anonymised; it collects no free text. No production system is probed.

## Honest limitations
Synthetic data encodes the authors' assumptions about fraud; reported performance is *method validation*, not market
prevalence. Survey data included in the repository is synthetic until replaced by real responses. See Chapter 6.
