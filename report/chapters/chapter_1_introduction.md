# Chapter 1 - Introduction

## 1.1 Background
FinTech services concentrate payments, identity and personal data in software that is continuously attacked. Providers deploy fraud models and
threat monitoring, yet adoption depends on consumer **trust**, which reflects perceived as well as actual security (McKnight et al., 2002; Gefen et al., 2003).

## 1.2 Problem statement
Fraud detection research optimises predictive metrics; trust research uses surveys. Few studies connect measured security performance, operational
monitoring and perceived trust in one reproducible system.

## 1.3 Aim and objectives
Aim: build and evaluate a reproducible platform linking fraud/threat detection with consumer trust. Objectives O1-O6 are listed in
`documentation/project_overview.md`; research questions RQ1-RQ7 in `documentation/research_questions.md`.

## 1.4 Scope and ethics
Synthetic data in an isolated environment, optional licensed public data, voluntary pseudonymised survey. No production systems are tested.

## 1.5 Contributions
1. An end-to-end, containerised, tested pipeline with leakage-safe features and a chronological protocol.
2. A fraud/anomaly model comparison emphasising false-positive cost.
3. A transparent Consumer Trust Score and a proposed Consumer Trust Index with sensitivity analysis.
4. An observability layer (Prometheus, Grafana, Loki) that exposes real experiment data rather than static visuals.

## 1.6 Report structure
Ch. 2 literature; Ch. 3 methodology; Ch. 4 implementation; Ch. 5 results; Ch. 6 conclusion, limitations, future work.
