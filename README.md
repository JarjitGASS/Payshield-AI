# 🛡 PayShield AI
### Agentic Risk Co-Pilot for Synthetic Identity Detection

> **Hackathon Build** · 48 Hours · Alibaba Cloud × Qwen · React + FastAPI + Docker

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Stack: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](backend/)
[![Stack: React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite%20%2B%20TS-61DAFB?logo=react)](frontend/)
[![AI: Qwen](https://img.shields.io/badge/AI-Qwen%20%40%20Alibaba%20Model%20Studio-FF6A00)](docs/PROMPT_ENGINEERING.md)

---

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Core Features](#-core-features)
3. [System Architecture](#-system-architecture)
4. [Repository Structure](#-repository-structure)
5. [Quick Start](#-quick-start)
6. [Documentation Index](#-documentation-index)
7. [Environment Variables](#-environment-variables)
8. [API Contract Summary](#-api-contract-summary)
9. [48-Hour Sprint Plan](#-48-hour-sprint-plan)
10. [Grading Alignment](#-grading-alignment)
11. [Team & Contributing](#-team--contributing)

---

## 🧩 Project Overview

**PayShield AI** is an **Agentic AI Risk Co-Pilot** built to detect **synthetic identities**, **mule accounts**, and **bot-driven onboarding** in digital payment ecosystems.

The core problem:

| Traditional Systems | PayShield AI |
|---|---|
| Static rule engines | Agentic LLM reasoning |
| Black-box ML scores | Explainable decisions |
| Binary approve/reject | APPROVE / REVIEW / REJECT |
| No behavioral signals | Biometric + behavioral analysis |
| No human oversight | Human-in-the-loop by design |

**Key differentiators:**
- 🤖 **Meta-Agent Orchestration** — Three specialized AI agents coordinated by a Qwen-powered meta-agent
- 🧠 **Explainable Decisions** — Every decision comes with structured reasoning anchored to real signals
- 🛡 **5-Layer Hallucination Guard** — Evidence-bounded prompts, JSON validation, deterministic config, guardrail policy, advisory-only AI
- 👤 **Human-in-the-Loop** — REVIEW queue + analyst dashboard with override capability

---

## ✨ Core Features

### 1. Customer Legitimacy Scoring
- **KTP (ID Card) Data Verification** — Cross-check inputted user data against KTP fields
- **Face Match** — KTP photo vs live user selfie using vision model comparison
- **Entity Legitimacy Check** — Scrape and sentiment-analyze user + company public presence

### 2. Behavioral Biometrics
- **Typing Cadence** — Keystroke timing variance analysis
- **Mouse Movement Entropy** — Movement randomness scoring
- **Navigation Consistency** — Page flow and interaction pattern consistency
- **Session Timing Patterns** — Login time anomaly detection

### 3. Identity Consistency Engine
- **Name vs Email Pattern** — Detect mismatched naming conventions
- **Phone Prefix vs Country** — Validate phone carrier prefix against declared country
- **Address vs IP / Device Location** — Geo-IP mismatch detection
- **Age vs Behavior Profile** — Behavioral age-consistency analysis

### 4. Synthetic Identity Detection Engine
- AI model reasoning over partially valid, mixed-source identity data
- Cross-account shared signal detection (phone, device, IP reuse)
- Rapid account creation pattern flagging

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────┐
│              React + Vite + TS              │
│         Analyst Dashboard / Onboarding UI   │
└─────────────────┬───────────────────────────┘
                  │ HTTPS REST
┌─────────────────▼───────────────────────────┐
│              FastAPI Backend                │
│  ┌──────────────────────────────────────┐   │
│  │       Feature Extraction Layer       │   │
│  │  (Identity • Behavioral • Network)   │   │
│  └──────────────┬───────────────────────┘   │
│  ┌──────────────▼───────────────────────┐   │
│  │     Qwen Agentic Risk Engine         │   │
│  │  ┌────────────┐  ┌───────────────┐   │   │
│  │  │ Identity   │  │  Behavioral   │   │   │
│  │  │ Risk Agent │  │ Anomaly Agent │   │   │
│  │  └─────┬──────┘  └──────┬────────┘   │   │
│  │        │   ┌────────────┘           │   │
│  │  ┌─────▼───▼──────────────────┐    │   │
│  │  │  Synthetic Network Agent   │    │   │
│  │  └─────────────┬──────────────┘    │   │
│  │  ┌─────────────▼──────────────┐    │   │
│  │  │   Meta-Agent Orchestrator  │    │   │
│  │  │       (Qwen LLM)           │    │   │
│  │  └─────────────┬──────────────┘    │   │
│  └────────────────┼───────────────────┘   │
│  ┌────────────────▼───────────────────┐   │
│  │    Policy Guardrail Layer          │   │
│  │  Score Range → APPROVE/REVIEW/REJECT│  │
│  └────────────────┬────────────────────┘  │
└───────────────────┼─────────────────────── ┘
                    │
┌───────────────────▼─────────────────────────┐
│         SQLite / PostgreSQL Database        │
│  Applications • Decisions • Analyst Logs    │
└─────────────────────────────────────────────┘
```

**Hosting:** Single Alibaba Cloud ECS instance · Docker Compose · Qwen API (Model Studio)

---

## 📁 Repository Structure

```
payshield-ai/
├── README.md                        ← You are here
├── docker-compose.yml               ← Full stack orchestration
├── .env.example                     ← Environment variable template
│
├── backend/                         ← FastAPI Python application
│   ├── README.md                    ← Backend-specific guide
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                      ← FastAPI entry point
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── applications.py  ← Onboarding submission endpoint
│   │   │   │   ├── decisions.py     ← Decision retrieval
│   │   │   │   └── analyst.py       ← Human override endpoints
│   │   ├── agents/
│   │   │   ├── identity_agent.py    ← Identity Risk Agent
│   │   │   ├── behavioral_agent.py  ← Behavioral Anomaly Agent
│   │   │   ├── network_agent.py     ← Synthetic Network Agent
│   │   │   └── meta_orchestrator.py ← Qwen Meta-Agent
│   │   ├── extractors/
│   │   │   ├── identity_extractor.py
│   │   │   ├── behavioral_extractor.py
│   │   │   └── network_extractor.py
│   │   ├── guardrails/
│   │   │   └── policy_layer.py      ← Guardrail + policy enforcement
│   │   ├── models/
│   │   │   ├── schemas.py           ← Pydantic request/response models
│   │   │   └── db_models.py         ← SQLAlchemy ORM models
│   │   └── db/
│   │       ├── database.py          ← DB connection setup
│   │       └── migrations/
│
├── frontend/                        ← React + Vite + TypeScript
│   ├── README.md                    ← Frontend-specific guide
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── OnboardingPage.tsx   ← User registration form
│   │   │   ├── DashboardPage.tsx    ← Analyst main dashboard
│   │   │   └── ReviewQueuePage.tsx  ← REVIEW state queue
│   │   ├── components/
│   │   │   ├── RiskMeter.tsx        ← Visual risk score gauge
│   │   │   ├── AgentBreakdown.tsx   ← Per-agent score cards
│   │   │   ├── DecisionBadge.tsx    ← APPROVE/REVIEW/REJECT badge
│   │   │   ├── AnalystOverride.tsx  ← Override form + notes
│   │   │   └── BiometricCapture.tsx ← Keystroke/mouse tracker
│   │   ├── hooks/
│   │   │   ├── useBiometrics.ts     ← Behavioral signal collection
│   │   │   └── useRiskAssessment.ts ← API integration hook
│   │   └── types/
│   │       └── risk.types.ts        ← Shared TypeScript types
│
└── docs/
    ├── ARCHITECTURE.md              ← Deep system design
    ├── PROMPT_ENGINEERING.md        ← Qwen prompt templates
    ├── DATABASE_SCHEMA.md           ← Full DB schema + ERD
    ├── DOCKER_SETUP.md              ← Docker + ECS deployment
    └── DEVELOPMENT_GUIDE.md         ← 48-hr sprint breakdown
```

---

## 🚀 Quick Start

### Prerequisites

- Docker + Docker Compose
- Node.js 20+ (for local frontend dev)
- Python 3.11+ (for local backend dev)
- Alibaba Cloud Model Studio API key (Qwen access)

### 1. Clone and Configure

```bash
git clone https://github.com/JarjitGASS/Payshield-AI.git
cd Payshield-AI
cp .env.example .env
# Edit .env and fill in QWEN_API_KEY and other values
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend (React) | http://localhost:5173 |
| Backend API (FastAPI) | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

### 3. Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 📚 Documentation Index

| Document | Description |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full system design, agent interaction diagrams, data flow |
| [`docs/PROMPT_ENGINEERING.md`](docs/PROMPT_ENGINEERING.md) | Qwen prompt templates, structured output schema, hallucination guards |
| [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md) | Full DB schema, table descriptions, ERD |
| [`docs/DOCKER_SETUP.md`](docs/DOCKER_SETUP.md) | Docker Compose config, Alibaba ECS deployment guide |
| [`docs/DEVELOPMENT_GUIDE.md`](docs/DEVELOPMENT_GUIDE.md) | 48-hour sprint task breakdown, API contracts, dev workflow |
| [`backend/README.md`](backend/README.md) | Backend setup, route reference, agent engine details |
| [`frontend/README.md`](frontend/README.md) | Frontend setup, component guide, biometric capture |

---

## 🔐 Environment Variables

Create a `.env` file from `.env.example`:

```env
# ── Qwen / Alibaba Model Studio ──────────────────────────
QWEN_API_KEY=your_alibaba_model_studio_api_key
QWEN_MODEL=qwen-max
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# ── Backend ───────────────────────────────────────────────
DATABASE_URL=sqlite:///./payshield.db
# For PostgreSQL: postgresql://user:password@db:5432/payshield
SECRET_KEY=your_secret_key_here
ENVIRONMENT=development

# ── CORS ─────────────────────────────────────────────────
FRONTEND_URL=http://localhost:5173

# ── Feature Flags ─────────────────────────────────────────
ENABLE_FACE_MATCH=true
ENABLE_ENTITY_SCRAPE=false   # Disable in dev to avoid rate limits
```

---

## 📡 API Contract Summary

### `POST /api/v1/applications/submit`
Submit new onboarding application for risk assessment.

**Request Body:**
```json
{
  "user": {
    "full_name": "string",
    "email": "string",
    "phone": "string",
    "date_of_birth": "YYYY-MM-DD",
    "address": "string",
    "country": "string",
    "ktp_number": "string"
  },
  "company": {
    "name": "string",
    "registration_number": "string"
  },
  "biometrics": {
    "typing_cadence_ms": [120, 95, 130, 88],
    "mouse_entropy_score": 0.72,
    "session_duration_sec": 145,
    "navigation_path": ["home", "register", "identity", "submit"]
  },
  "device": {
    "ip_address": "string",
    "user_agent": "string",
    "device_fingerprint": "string"
  },
  "ktp_image_base64": "string (optional)",
  "selfie_image_base64": "string (optional)"
}
```

**Response:**
```json
{
  "application_id": "uuid",
  "identity_risk": 0.25,
  "behavior_risk": 0.10,
  "network_risk": 0.05,
  "overall_risk": 0.18,
  "decision": "APPROVE",
  "confidence": 0.88,
  "explanation": "Identity signals are consistent. Behavioral patterns match expected human interaction. No network reuse detected.",
  "agent_details": {
    "identity": { "score": 0.25, "flags": [] },
    "behavioral": { "score": 0.10, "flags": [] },
    "network": { "score": 0.05, "flags": [] }
  }
}
```

### `GET /api/v1/decisions/review-queue`
Fetch all applications in REVIEW state for analyst dashboard.

### `POST /api/v1/analyst/override`
Submit human analyst decision override.

**Request Body:**
```json
{
  "application_id": "uuid",
  "human_decision": "CONFIRMED_FRAUD | CLEARED | NEEDS_MORE_INFO",
  "analyst_note": "string"
}
```

> See [`docs/DEVELOPMENT_GUIDE.md`](docs/DEVELOPMENT_GUIDE.md) for complete API contract with all endpoints.

---

## ⏱ 48-Hour Sprint Plan

| Hour | Milestone |
|---|---|
| 0–4 | Repo setup, Docker Compose, env config, DB init |
| 4–10 | Backend: FastAPI skeleton, DB models, feature extractors |
| 10–18 | Qwen agent engine: identity + behavioral + network agents + meta-orchestrator |
| 18–22 | Guardrail + policy layer, API endpoints complete |
| 22–28 | Frontend: Onboarding form, biometric capture hooks |
| 28–34 | Frontend: Analyst dashboard, risk meter, agent breakdown cards |
| 34–38 | Human-in-the-loop: REVIEW queue, analyst override UI |
| 38–44 | Integration testing, edge case handling, demo data seeding |
| 44–48 | Polish UI, record demo, prepare pitch |

> Full task breakdown with acceptance criteria: [`docs/DEVELOPMENT_GUIDE.md`](docs/DEVELOPMENT_GUIDE.md)

---

## 🏆 Grading Alignment

| Criterion | Weight | How PayShield AI Addresses It |
|---|---|---|
| **Value & Innovation** | 25% | Agentic AI reasoning, synthetic identity graph, multi-signal intelligence, human-AI collaboration |
| **Design & UX** | 25% | Risk dashboard, agent breakdown cards, risk meter visualization, manual override interface |
| **AI Utilization** | 30% | Meta-agent orchestration via Qwen, explainability generation, 5-layer hallucination control, confidence-based escalation |
| **Impact & Implementation** | 20% | Reduces fraud, protects merchants, improves compliance, prevents financial exclusion via REVIEW state, deployable on Alibaba Cloud |

---

## 👥 Team & Contributing

See [`docs/DEVELOPMENT_GUIDE.md`](docs/DEVELOPMENT_GUIDE.md) for branching strategy, PR conventions, and task assignments.

---

*PayShield AI — Powered by Qwen on Alibaba Cloud*
