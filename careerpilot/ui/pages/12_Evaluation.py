import streamlit as st
import json
import pandas as pd
import plotly.express as px
from careerpilot.evaluation.job_analysis_eval import evaluate_job_analysis
from careerpilot.evaluation.rag_eval import evaluate_rag_retrieval
from careerpilot.evaluation.truth_guard_eval import evaluate_truth_guard
from careerpilot.evaluation.resume_eval import evaluate_resume_generation
from careerpilot.evaluation.interview_eval import evaluate_interview_engine
from careerpilot.evaluation.regression import run_regression_suite
from careerpilot.observability.tracer import tracer

st.set_page_config(page_title="AI Evaluation & Observability — CareerPilot AI", page_icon="📊", layout="wide")

from careerpilot.services.auth_service import AuthService
from careerpilot.core.config import settings

if not settings.is_demo_mode:
    AuthService.require_auth()


st.markdown("""
<div style="background-color: #f8f9fa; border-left: 5px solid #6366f1; padding: 1.2rem; border-radius: 6px; margin-bottom: 1.5rem;">
    <h2 style="margin: 0; color: #1e1b4b; display: flex; align-items: center; gap: 0.6rem;">
        📊 AI Evaluation, RAG Quality & Observability Dashboard
    </h2>
    <p style="margin: 0.4rem 0 0 0; color: #4b5563; font-size: 0.95rem;">
        <b>Developer / Evaluation Mode:</b> Empirical benchmark metrics, retrieval evaluations, Truth Guard confusion matrices, latency distributions, and live workflow traces.
    </p>
</div>
""", unsafe_allow_html=True)

# Run or Load Evaluations
if "eval_results" not in st.session_state:
    with st.spinner("Running initial evaluation benchmarks..."):
        job_res = evaluate_job_analysis()
        rag_res = evaluate_rag_retrieval()
        tg_res = evaluate_truth_guard()
        res_res = evaluate_resume_generation()
        int_res = evaluate_interview_engine()
        reg_res = run_regression_suite()
        st.session_state["eval_results"] = {
            "job": job_res,
            "rag": rag_res,
            "tg": tg_res,
            "resume": res_res,
            "interview": int_res,
            "regression": reg_res,
        }

eval_data = st.session_state["eval_results"]
job_res = eval_data["job"]
rag_res = eval_data["rag"]
tg_res = eval_data["tg"]
res_res = eval_data["resume"]
int_res = eval_data["interview"]
reg_res = eval_data["regression"]

# Top High-Level Metrics
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    cand_r5 = rag_res.get("candidate_evidence_rag", {}).get("recall@5", 0.0) * 100
    st.metric("RAG Recall@5", f"{cand_r5:.1f}%", help="Candidate store top-5 recall across ground truth queries")
with col2:
    cand_mrr = rag_res.get("candidate_evidence_rag", {}).get("mrr", 0.0)
    st.metric("RAG MRR", f"{cand_mrr:.3f}", help="Mean Reciprocal Rank of first relevant chunk")
with col3:
    tg_f1 = tg_res.get("f1_score", 0.0) * 100
    st.metric("Truth Guard F1", f"{tg_f1:.1f}%", help="Harmonic mean of precision and recall for hallucination blocking")
with col4:
    job_acc = job_res.get("role_classification_accuracy", 0.0) * 100
    st.metric("Role Classifier Acc", f"{job_acc:.1f}%", help="Role taxonomy classification accuracy across 10 benchmark jobs")
with col5:
    reg_status = reg_res.get("status", "PASS")
    st.metric("Regression Status", reg_status, delta="Passed" if reg_status == "PASS" else "Alert", delta_color="normal")

st.markdown("---")

# Main Evaluation Tabs
tabs = st.tabs([
    "🔍 RAG & Retrieval Quality",
    "🛡️ Truth Guard Benchmark",
    "📋 Job Analysis Evaluation",
    "⏱️ Latency & Observability",
    "🔄 Live Event Trace",
])

# -------------------------------------------------------------
# Tab 1: RAG & Retrieval Quality
# -------------------------------------------------------------
with tabs[0]:
    st.subheader("Dual-Store RAG Performance & Method Comparison")
    
    col_c, col_k = st.columns(2)
    with col_c:
        st.markdown("#### Candidate Evidence Store")
        c_metrics = rag_res.get("candidate_evidence_rag", {})
        df_c = pd.DataFrame([
            {"Metric": "Recall@1", "Value": f"{c_metrics.get('recall@1', 0.0)*100:.1f}%"},
            {"Metric": "Recall@3", "Value": f"{c_metrics.get('recall@3', 0.0)*100:.1f}%"},
            {"Metric": "Recall@5", "Value": f"{c_metrics.get('recall@5', 0.0)*100:.1f}%"},
            {"Metric": "Precision@5", "Value": f"{c_metrics.get('precision@5', 0.0)*100:.1f}%"},
            {"Metric": "MRR (Mean Reciprocal Rank)", "Value": f"{c_metrics.get('mrr', 0.0):.3f}"},
            {"Metric": "Retrieval Errors", "Value": str(c_metrics.get('errors_count', 0))},
        ])
        st.dataframe(df_c, hide_index=True, use_container_width=True)

    with col_k:
        st.markdown("#### Technical Knowledge Store")
        k_metrics = rag_res.get("technical_knowledge_rag", {})
        df_k = pd.DataFrame([
            {"Metric": "Recall@1", "Value": f"{k_metrics.get('recall@1', 0.0)*100:.1f}%"},
            {"Metric": "Recall@3", "Value": f"{k_metrics.get('recall@3', 0.0)*100:.1f}%"},
            {"Metric": "Recall@5", "Value": f"{k_metrics.get('recall@5', 0.0)*100:.1f}%"},
            {"Metric": "Precision@5", "Value": f"{k_metrics.get('precision@5', 0.0)*100:.1f}%"},
            {"Metric": "MRR (Mean Reciprocal Rank)", "Value": f"{k_metrics.get('mrr', 0.0):.3f}"},
            {"Metric": "Retrieval Errors", "Value": str(k_metrics.get('errors_count', 0))},
        ])
        st.dataframe(df_k, hide_index=True, use_container_width=True)

    st.markdown("#### Retrieval Method Comparison (Vector vs BM25 vs Hybrid RRF)")
    m_comp = rag_res.get("retrieval_method_comparison", {})
    comp_rows = []
    for method, data in m_comp.items():
        comp_rows.append({
            "Method": method.replace("_", " ").title(),
            "MRR": data.get("mrr", 0.0),
            "Recall@5": f"{data.get('recall@5', 0.0)*100:.1f}%",
            "Characteristics": data.get("notes", ""),
        })
    st.dataframe(pd.DataFrame(comp_rows), hide_index=True, use_container_width=True)

# -------------------------------------------------------------
# Tab 2: Truth Guard Benchmark
# -------------------------------------------------------------
with tabs[1]:
    st.subheader("Deterministic Truth Guard Confusion Matrix & Audit Cases")
    
    cm = tg_res.get("confusion_matrix", {})
    col_cm1, col_cm2, col_cm3, col_cm4 = st.columns(4)
    with col_cm1:
        st.metric("True Positives (Blocked Hallucinations)", cm.get("true_positives", 0))
    with col_cm2:
        st.metric("True Negatives (Passed Ground Truth)", cm.get("true_negatives", 0))
    with col_cm3:
        st.metric("False Positives (False Alarms)", cm.get("false_positives", 0))
    with col_cm4:
        st.metric("False Negatives (Missed Fabrications)", cm.get("false_negatives", 0))

    st.markdown("#### 12-Case Golden Audit Breakdown")
    cases = tg_res.get("case_breakdown", [])
    if cases:
        case_rows = []
        for c in cases:
            case_rows.append({
                "Case ID": c["case_id"],
                "Description": c["description"],
                "Expected": c["expected_verdict"],
                "Actual": c["actual_verdict"],
                "Outcome": c["outcome"],
                "Blocked Reasons": "; ".join(c.get("blocked_reasons", [])) or "None (Clean Pass)",
            })
        st.dataframe(pd.DataFrame(case_rows), hide_index=True, use_container_width=True)

# -------------------------------------------------------------
# Tab 3: Job Analysis Evaluation
# -------------------------------------------------------------
with tabs[2]:
    st.subheader("Job Analysis & Extraction Quality (10 Golden Benchmark Jobs)")
    
    col_j1, col_j2, col_j3 = st.columns(3)
    with col_j1:
        st.metric("Role Classification Accuracy", f"{job_res.get('role_classification_accuracy', 0.0)*100:.1f}%")
    with col_j2:
        st.metric("Seniority Detection Accuracy", f"{job_res.get('seniority_detection_accuracy', 0.0)*100:.1f}%")
    with col_j3:
        st.metric("Must-Have Skill Avg F1", f"{job_res.get('must_have_extraction_avg_f1', 0.0)*100:.1f}%")

    st.markdown("#### Extraction Performance Breakdown")
    st.dataframe(pd.DataFrame([
        {"Extraction Component": "Role Category Classification", "Metric": "Accuracy", "Score": f"{job_res.get('role_classification_accuracy', 0.0)*100:.1f}%"},
        {"Extraction Component": "Seniority Level Detection", "Metric": "Accuracy", "Score": f"{job_res.get('seniority_detection_accuracy', 0.0)*100:.1f}%"},
        {"Extraction Component": "Must-Have Requirements", "Metric": "Average F1", "Score": f"{job_res.get('must_have_extraction_avg_f1', 0.0)*100:.1f}%"},
        {"Extraction Component": "Nice-to-Have Requirements", "Metric": "Average F1", "Score": f"{job_res.get('nice_to_have_extraction_avg_f1', 0.0)*100:.1f}%"},
        {"Extraction Component": "Core Technology Entities", "Metric": "Average F1", "Score": f"{job_res.get('technology_extraction_avg_f1', 0.0)*100:.1f}%"},
    ]), hide_index=True, use_container_width=True)

# -------------------------------------------------------------
# Tab 4: Latency & Observability
# -------------------------------------------------------------
with tabs[3]:
    st.subheader("Execution Latency Distributions & Token Telemetry")
    
    latencies = tracer.get_latency_summary()
    if latencies:
        lat_rows = []
        for op, stats in latencies.items():
            lat_rows.append({
                "Operation": op,
                "Sample Count": stats["count"],
                "Min (ms)": stats["min_ms"],
                "Average (ms)": stats["avg_ms"],
                "Median (ms)": stats["median_ms"],
                "P95 (ms)": stats["p95_ms"],
            })
        df_lat = pd.DataFrame(lat_rows)
        st.dataframe(df_lat, hide_index=True, use_container_width=True)

        fig = px.bar(df_lat, x="Operation", y="P95 (ms)", title="P95 Latency by Subsystem (Milliseconds)", color="P95 (ms)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No latency traces recorded yet. Run a workflow to populate latency metrics.")

    st.markdown("#### LLM Token Usage & Cost Model")
    cost_summary = tracer.get_token_and_cost_summary()
    st.json(cost_summary)

# -------------------------------------------------------------
# Tab 5: Live Event Trace
# -------------------------------------------------------------
with tabs[4]:
    st.subheader("Live Workflow Event Traces (Zero PII Recorded)")
    
    recent_traces = tracer.get_recent_traces(limit=30)
    if recent_traces:
        trace_df = pd.DataFrame([
            {
                "Trace ID": t["trace_id"],
                "Event Type": t["event_type"],
                "Operation": t["operation"],
                "Duration (ms)": t["duration_ms"],
                "Status": t["status"],
            }
            for t in recent_traces
        ])
        st.dataframe(trace_df, hide_index=True, use_container_width=True)
    else:
        st.info("No trace events currently in buffer.")

st.markdown("---")
if st.button("🔄 Re-run All Evaluation Benchmarks", use_container_width=True):
    with st.spinner("Re-executing evaluation suite..."):
        st.session_state["eval_results"] = {
            "job": evaluate_job_analysis(),
            "rag": evaluate_rag_retrieval(),
            "tg": evaluate_truth_guard(),
            "resume": evaluate_resume_generation(),
            "interview": evaluate_interview_engine(),
            "regression": run_regression_suite(),
        }
    st.success("Evaluation suite refreshed with latest live measurements!")
    st.rerun()
