# CareerPilot AI — Live Demo Walkthrough Script

**Audience:** Technical Recruiters, Engineering Hiring Managers, AI Systems Interviewers  
**Duration:** 5–10 Minutes  
**Mode:** `DEMO` Mode (Operating on synthetic candidate **Alex Rivera** — 100% public, safe, and reproducible)  

---

## Pre-Demo Checklist
- [ ] Run `streamlit run careerpilot/ui/app.py` in terminal.
- [ ] Verify Demo Mode badge is visible: `🌐 Environment: DEMO MODE (Alex Rivera)`.
- [ ] Ensure browser is opened at `http://localhost:8501`.

---

## Step-by-Step Demo Flow

### Step 1: Platform Overview & System Health (1 Minute)
1. **Navigate to:** `Welcome Screen / Dashboard`.
2. **Talking Points:**
   - *"CareerPilot AI is an autonomous, evidence-grounded career copilot. Unlike generic chatbot wrappers that hallucinate nonexistent skills, CareerPilot grounds every recommendation, resume bullet, and interview question in verified candidate evidence."*
3. **Show:** Click the **🩺 System Diagnostics & Health Status** expander. Show that all 7 subsystems (ChromaDB, SQLite, Embeddings, LLM fallback) are operational.

---

### Step 2: Job Analysis & Deterministic Fit Scoring (2 Minutes)
1. **Navigate to:** `2_Analyze_Job.py` in the left sidebar.
2. **Action:** Click the **"📂 Load Evaluation Benchmark"** tab and select `01_ai_data_engineer.txt`.
3. **Action:** Click **"🚀 Analyze Job Description"**.
4. **Show & Explain:**
   - **Role & Reality Classification:** Explain that while the job title says *"Senior AI Data Platform Engineer"*, the work distribution classifier analyzes the actual responsibilities (53.8% Data Eng, 30.8% GenAI, 15.4% Cloud).
   - **Fit Score & Recommendation:** Point out the deterministic fit score (**85.0%**) and the **APPLY** recommendation.
   - **Must-Have vs Nice-to-Have Requirements:** Show how core skills (Python, SQL, BigQuery, Airflow) match verified evidence.

---

### Step 3: Truth-Guarded Resume Tailoring & ATS Export (2 Minutes)
1. **Navigate to:** `4_Resume_Builder.py`.
2. **Action:** Select the newly analyzed application, choose the **AI Data Engineer** strategy, and click **"✨ Generate Tailored Resume"**.
3. **Show & Explain:**
   - **Truth Guard Report:** Expand the Truth Guard tab. Show `Status: PASS` with `0 Blocked Claims` and `0 Hallucinations`.
   - **Project Boundary Isolation:** Show that the candidate's personal RAG project remains strictly in the `Projects` section and is not disguised as enterprise client work.
   - **Download Clean DOCX:** Click **"📥 Download ATS DOCX Resume"** to show instant generation of a table-free, ATS-safe `.docx` document.

---

### Step 4: Explainable ATS Compatibility Analysis (1.5 Minutes)
1. **Navigate to:** `5_ATS_Analysis.py`.
2. **Show & Explain:**
   - **Overall ATS Score:** Point out the 7-component transparent score (**96.7%**).
   - **Keyword Coverage Matrix:** Show the exact match breakdown across must-haves (BigQuery, Airflow, Python) and nice-to-haves.
   - **Anti-Stuffing Audit:** Highlight the zero-risk verdict for keyword density and clean formatting structure.

---

### Step 5: Deep Interview Preparation & Study Roadmap (1.5 Minutes)
1. **Navigate to:** `6_Interview_Prep.py`.
2. **Action:** Select 3-Day Roadmap and click **"📚 Generate Interview Prep Plan"**.
3. **Show & Explain:**
   - **Multi-Category Q&A:** Browse Technical Concepts, System Design, and STAR Behavioral stories.
   - **Tiered Answers:** Show how each question provides Short (30s), Standard (90s), and Deep Dive (3min) answers.
   - **Transferable Gap Framing:** Show how missing AWS tools are framed honestly as conceptual transfers from GCP BigQuery.

---

### Step 6: Interactive Adaptive Mock Interview (2 Minutes)
1. **Navigate to:** `7_Mock_Interview.py`.
2. **Action:** Select `Technical Only` mode, `Senior Engineer` persona, `Coaching Mode`, and click **"🎙️ Start Mock Interview"**.
3. **Action:** Submit an answer to Question 1:
   > *"At Apex Cloud Solutions, I designed and optimized automated ETL pipelines in BigQuery and Airflow processing 2.5M+ daily records."*
4. **Show & Explain:**
   - **Turn Evaluation:** Show the instant 10-dimensional rubric feedback (Technical Correctness: 90, Evidence Grounding: 95).
   - **Adaptive Branching:** Show how the agent asks a challenging follow-up question based on the candidate's specific answer.
5. **Action:** Click **"🏁 Finish Interview & Generate Report"**.
6. **Show:** Point out the overall scorecard, strengths, and targeted study priorities.

---

## Demo Conclusion
- *"That concludes the end-to-end CareerPilot workflow: from raw job posting to truthful tailored resume, ATS audit, deep interview prep, and live adaptive simulation—built entirely on deterministic software guardrails and stateful LangGraph orchestration."*
