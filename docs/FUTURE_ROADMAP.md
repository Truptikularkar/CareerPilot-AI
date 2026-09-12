# CareerPilot AI — Future Product & Engineering Roadmap

**Document:** `docs/FUTURE_ROADMAP.md`  
**Classification:** Phased Architecture Evolution & Engineering Roadmap  
**Notice:** *This document outlines potential future architectural enhancements for future development cycles.*

---

## Phased Evolution Strategy

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Phase 1 - 3     │ ────> │ Phase 4 - 6     │ ────> │ Phase 7 - 8     │ ────> │ Phase 9 - 10    │
│ Enterprise Core │       │ Multi-Tenancy   │       │ Voice & Multimodal│     │ Global Cloud    │
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
```

---

### Phase 1: Managed Relational Database Migration
- Upgrade local SQLite backend to **PostgreSQL 16** via Google Cloud SQL / Amazon RDS.
- Implement production database migrations with **Alembic** and multi-AZ failover replicas.

### Phase 2: Managed Distributed Vector Database
- Migrate local ChromaDB filesystem collections to **Google Vertex AI Vector Search** or **Pinecone**.
- Implement dynamic index sharding and sub-millisecond approximate nearest neighbor (ANN) retrieval.

### Phase 3: Multi-Tenant Authentication & Access Control
- Integrate **OAuth2 / OpenID Connect** (Google, GitHub, LinkedIn single sign-on).
- Implement role-based access control (RBAC) separating candidate personal workspaces from enterprise recruiter dashboards.

### Phase 4: Workspace Isolation & Data Encryption at Rest
- Add per-user customer managed encryption keys (CMEK) and strict multi-tenant row-level security (RLS) policies in PostgreSQL.

### Phase 5: Automated Job Board Integrations
- Build automated webhooks and browser extension connectors for 1-click JD importing from LinkedIn Jobs, Greenhouse, Lever, and Indeed.

### Phase 6: Application & Calendar Synchronization
- Integrate Google Calendar and Microsoft Outlook APIs for automatic scheduling of interview prep roadmaps and mock practice sessions.

### Phase 7: Real-Time Voice-Enabled Mock Interviews
- Implement bidirectional audio streaming using **WebRTC**, **OpenAI Whisper / Google Speech-to-Text**, and **Gemini Live Audio / ElevenLabs**.
- Allow candidates to conduct mock interviews entirely through conversational voice.

### Phase 8: Audio & Speech Delivery Analytics
- Analyze spoken candidate responses for speech pacing (words per minute), filler word frequency (*"um"*, *"like"*, *"you know"*), pauses, and vocal confidence.

### Phase 9: Automated RAG Evaluation Framework (Ragas / TruLens)
- Integrate automated RAG evaluation metrics (Context Precision, Context Recall, Faithfulness, and Answer Relevance) into CI/CD build pipelines.

### Phase 10: Cloud-Native Serverless Orchestration
- Package microservices into lightweight Docker containers deployed on **Google Cloud Run** or **AWS ECS Fargate** with distributed Redis caching and Google Cloud Tasks task queues.
