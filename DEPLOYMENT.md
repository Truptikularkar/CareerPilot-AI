# CareerPilot AI — Production Deployment Guide

This guide details how to deploy CareerPilot AI to **Streamlit Community Cloud**, **Hugging Face Spaces**, **Docker**, or on a **Local Server**.

---

## 1. Environment Modes Overview

CareerPilot AI supports two operational modes:

| Mode | Environment Variable | Target Use Case | Ground-Truth Data Source |
| :--- | :--- | :--- | :--- |
| **Public Portfolio Mode** | `CAREERPILOT_MODE=DEMO` | Public Cloud Deployments, Portfolio Showcases (Bypasses login) | `data/demo/` or `data/candidate/` (Verified profile) |
| **Local Private Mode** | `CAREERPILOT_MODE=LOCAL_PRIVATE` | Personal Local Machine Use (With Login Gatekeeper) | Canonical SQLite + `data/candidate/` |

---

## 2. Deploying to Streamlit Community Cloud

1. **Push your repository to GitHub** (ensure `.gitignore` excludes `.env` and `*.db`).
2. Navigate to [share.streamlit.io](https://share.streamlit.io/) and click **"New app"**.
3. Select your repository, branch (`main`), and set the main file path to:
   ```
   careerpilot/ui/app.py
   ```
4. Click **"Advanced settings..."** -> **Secrets** and configure your secrets:
   ```toml
   CAREERPILOT_MODE = "DEMO"
   GEMINI_API_KEY = "your-gemini-api-key"
   GEMINI_MODEL = "gemini-3.6-flash"
   LLM_PROVIDER = "gemini"
   ```
5. Click **Deploy!**

---

## 3. Deploying with Docker

A production container can be built and run using the following instructions:

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose Streamlit port
EXPOSE 8501

ENV CAREERPILOT_MODE=DEMO
ENV PYTHONUNBUFFERED=1

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "careerpilot/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Build & Run Commands
```bash
# Build the container image
docker build -t careerpilot-ai:latest .

# Run the container in DEMO mode
docker run -d -p 8501:8501 --name careerpilot careerpilot-ai:latest

# Or run with your personal Gemini API key
docker run -d -p 8501:8501 -e GEMINI_API_KEY="your-api-key" careerpilot-ai:latest
```

---

## 4. Deploying to Hugging Face Spaces

1. Create a new Space on [huggingface.co/spaces](https://huggingface.co/spaces) selecting the **Streamlit** SDK.
2. Push your project files to the Hugging Face Git remote.
3. In Space Settings -> **Variables and Secrets**:
   - Add Secret: `GEMINI_API_KEY` (Optional)
   - Add Variable: `CAREERPILOT_MODE = DEMO`
4. The space will automatically install dependencies from `requirements.txt` and launch `careerpilot/ui/app.py`.

---

## 5. Local Setup & Quickstart

```bash
# 1. Clone the repository
git clone https://github.com/your-username/careerpilot-ai.git
cd careerpilot-ai

# 2. Create and activate a Python virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env

# 5. Run the local Streamlit application
streamlit run careerpilot/ui/app.py
```
