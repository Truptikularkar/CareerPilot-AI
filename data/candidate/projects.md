# Projects — Source of Truth

## 1. AI-Driven Data Quality Monitoring & Anomaly Detection
**Technologies:** BigQuery ML, SQL, Gemini 2.5 Pro

Verified evidence:
- Built an AI-driven anomaly detection system using BigQuery ML Linear Regression with IQR-based adaptive thresholds.
- Replaced hardcoded rules.
- Achieved approximately 92% anomaly detection accuracy.
- False positive rate under 5% across 6 months of backtested data.
- Integrated Gemini 2.5 Pro via Vertex AI for automated root-cause analysis.
- Reduced mean investigation time from approximately 45 minutes to under 5 minutes.
- Enabled real-time data quality monitoring at scale.

## 2. Local RAG & Hybrid Retrieval Sandbox
**Technologies:** Python, FAISS, BM25, Google Gemini API, Ollama

Verified evidence:
- Built a locally deployable RAG playground.
- Combined dense FAISS and sparse BM25 retrieval using Reciprocal Rank Fusion.
- Implemented configurable chunking.
- Added visual pipeline tracing for ranks and relevance scores.
- Built a provider-agnostic generation layer supporting Gemini API, local Ollama models, and offline simulation.
- Intended to enable LLM orchestration testing without recurring cloud costs.

Important:
This is personal/project experience, not client production experience.

## 3. AI AutoHeal Agent — Automated Job Failure Remediation
**Technologies:** GCP Cloud Run, BigQuery, Airflow, Gemini 2.5 Pro, Python, SQL

Verified evidence:
- Architected an autonomous AI agent on GCP Cloud Run.
- Detected Airflow DAG failures from BigQuery.
- Used Gemini 2.5 Pro classification to auto-remediate recoverable issues.
- Resolved approximately 75% of transient failures without human intervention.
- Reduced on-call response time by approximately 60%.
- Implemented a data-quality guardrail blocking auto-remediation for integrity-related failures.
- Built end-to-end NDJSON audit tracking loaded into BigQuery.
- Achieved 100% job-level traceability across remediation events.

## 4. Automated Sales Data Validation DAG
**Technologies:** Apache Airflow, BigQuery, SQL, Python, Power Automate

Verified evidence:
- Engineered configurable Airflow pipeline for sales data validation across source and target systems.
- Used CTE-based SQL variance logic.
- Implemented BigQuery audit logging.
- Reduced manual validation effort by approximately 70%.
- Caught discrepancies within minutes instead of hours.
- Used dag_run.conf for dynamic runtime configuration.
- Enabled zero-code onboarding of new validation workflows.
- Reduced setup time from days to under 30 minutes.
- Integrated Microsoft Teams alerts through Power Automate REST API.

## 5. CareerPilot AI — Multi-Agent Autonomous Career Copilot & RAG Job Platform
**Technologies:** Python, LangGraph, Google Gemini API (gemini-3.6-flash), ChromaDB, Streamlit Cloud, SQLite, GitHub API, SQL, Pydantic

Verified evidence:
- Architected and deployed an end-to-end multi-agent AI system live on Streamlit Cloud using LangGraph cyclic state machines for autonomous job description analysis, resume tailoring, and interview preparation.
- Built a hybrid RAG retrieval pipeline with ChromaDB vector embeddings and BM25 sparse search, implementing strict ground-truth verification that prevents LLM hallucinations by cross-checking candidate claims against verified experience.
- Integrated Google Gemini 3.6-flash LLM to generate role-specific technical questionnaires across 3 difficulty tiers (Easy/Medium/Hard) and 4-6 hands-on coding & SQL challenges with complete executable solutions and complexity analysis.
- Designed a 9-dimension deterministic ATS match-scoring algorithm that parses requirements into Must-Have vs. Nice-to-Have skills, generating explainable recommendations (Apply, Review, Skip).
- Integrated GitHub REST API to automatically fetch, verify, and index public repositories and technical telemetry directly into candidate evidence stores.
- Built an interactive Streamlit UI featuring dynamic candidate profile editing, on-demand Gemini AI re-analysis, and complete Markdown interview guide generation.
