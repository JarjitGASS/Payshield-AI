# 🏃 PayShield AI — Development Guide

## 48-Hour Sprint Breakdown, API Contracts & Dev Workflow

---

## Table of Contents
1. [Team Roles Suggestion](#1-team-roles-suggestion)
2. [48-Hour Sprint Plan](#2-48-hour-sprint-plan)
3. [Git Workflow](#3-git-workflow)
4. [Complete API Contract](#4-complete-api-contract)
5. [Development Checklist](#5-development-checklist)
6. [Testing Strategy](#6-testing-strategy)
7. [Demo Preparation](#7-demo-preparation)

---

## 1. Team Roles Suggestion

| Role | Responsibilities | Primary Files |
|---|---|---|
| **Backend Dev (AI Engine)** | Agents, meta-orchestrator, Qwen integration, guardrails | `backend/app/agents/`, `backend/app/guardrails/` |
| **Backend Dev (API & DB)** | Routes, models, extractors, DB setup | `backend/app/api/`, `backend/app/models/`, `backend/app/db/` |
| **Frontend Dev** | All React pages, components, hooks | `frontend/src/` |
| **DevOps / Infra** | Docker Compose, `.env`, ECS setup, Nginx | `docker-compose.yml`, `frontend/nginx.conf` |

> For a 2-person team: Person A = Backend + AI Engine; Person B = Frontend + Docker.

---

## 2. 48-Hour Sprint Plan

### 🟦 Phase 1: Foundation (Hour 0–4)

**All developers:**

- [ ] Clone repo, create feature branches
- [ ] Copy `.env.example` → `.env`, fill in `QWEN_API_KEY`
- [ ] Run `docker-compose up --build` — verify all containers start

**Backend Dev:**
- [ ] Create `backend/` structure (all directories)
- [ ] Write `requirements.txt` and verify `pip install` works
- [ ] Set up `main.py` with FastAPI app, health endpoint, CORS
- [ ] Set up `app/db/database.py` and `app/models/db_models.py`
- [ ] Call `init_db()` on startup — confirm SQLite file is created
- [ ] Write `app/models/schemas.py` (all Pydantic models)

**Frontend Dev:**
- [ ] `npm create vite@latest frontend -- --template react-ts`
- [ ] Install dependencies (see `frontend/README.md`)
- [ ] Configure Tailwind CSS
- [ ] Set up `App.tsx` with React Router (3 routes)
- [ ] Create placeholder pages (OnboardingPage, DashboardPage, ReviewQueuePage)

**Acceptance Criteria:**
- `GET http://localhost:8000/health` → `{"status": "ok"}`
- `http://localhost:5173` → React app loads with navigation

---

### 🟦 Phase 2: Backend Core (Hour 4–10)

**Backend Dev (API & DB):**

- [ ] Implement `IdentityExtractor.extract()` (see `backend/README.md` §6)
- [ ] Implement `BehavioralExtractor.extract()`
- [ ] Implement `NetworkExtractor.extract()`
- [ ] Create stub `/api/v1/applications/submit` endpoint that returns a hardcoded mock response
- [ ] Create `GET /api/v1/decisions/review-queue` endpoint
- [ ] Create `POST /api/v1/analyst/override` endpoint
- [ ] Create `GET /api/v1/analyst/stats` endpoint
- [ ] Write mock `seed_demo.py` with 3 demo applications

**Acceptance Criteria:**
- `POST /api/v1/applications/submit` with valid payload → returns mocked `ApplicationResponse` JSON
- `GET /api/v1/decisions/review-queue` → returns array (empty or seeded)
- Swagger UI at `/docs` shows all routes

---

### 🟦 Phase 3: AI Agent Engine (Hour 10–18)

**Backend Dev (AI Engine):**

- [ ] Implement `IdentityAgent.analyze()` — real Qwen call + fallback
- [ ] Implement `BehavioralAgent.analyze()` — real Qwen call + fallback
- [ ] Implement `NetworkAgent.analyze()` — real Qwen call + fallback
- [ ] Implement `MetaOrchestrator.decide()` — real Qwen call + fallback
- [ ] Test each agent independently with `curl` or Jupyter notebook

**Test each agent:**
```bash
# Quick test: call identity agent directly
python -c "
from app.agents.identity_agent import IdentityAgent
result = IdentityAgent().analyze({
    'ktp_match_score': 0.9, 'face_similarity_score': 0.85,
    'email_age_days': 365, 'phone_reuse_count': 0,
    'geo_ip_mismatch': False, 'name_entropy': 3.2, 'entity_sentiment_score': 0.8
})
print(result)
"
```

**Acceptance Criteria:**
- Each agent returns valid JSON matching its schema
- Fallback works when `QWEN_API_KEY` is invalid (returns neutral 0.5 + REVIEW)
- Meta-orchestrator combines all three agents into final decision

---

### 🟦 Phase 4: Guardrails & Full Pipeline (Hour 18–22)

**Backend Dev (AI Engine + API):**

- [ ] Implement `PolicyLayer.enforce()` (see `backend/README.md` §9)
- [ ] Wire full pipeline into `POST /api/v1/applications/submit`:
  1. Extract features → 2. Run agents → 3. Meta-orchestrate → 4. Guardrail → 5. Persist → 6. Return
- [ ] Test full pipeline end-to-end with `curl`:

```bash
curl -X POST http://localhost:8000/api/v1/applications/submit \
  -H "Content-Type: application/json" \
  -d '{
    "user": {
      "full_name": "Test User", "email": "test@gmail.com",
      "phone": "+6281234567890", "ktp_number": "3174052505900001"
    },
    "device": {
      "ip_address": "103.10.20.30",
      "user_agent": "Mozilla/5.0",
      "device_fingerprint": "test_fp_001"
    }
  }'
```

- [ ] Seed demo data: `python seed_demo.py`

**Acceptance Criteria:**
- Full pipeline returns `ApplicationResponse` with real AI scores
- Guardrail triggers correctly on malformed AI output
- All 3 decision types (APPROVE/REVIEW/REJECT) can be produced

---

### 🟦 Phase 5: Frontend Onboarding (Hour 22–28)

**Frontend Dev:**

- [ ] Implement `useBiometrics.ts` hook (see `frontend/README.md` §6)
- [ ] Implement `useRiskAssessment.ts` API hooks
- [ ] Build `OnboardingPage.tsx`:
  - Step 1: Personal Info form (name, email, phone, DOB, country)
  - Step 2: KTP upload + selfie upload (base64 conversion)
  - Step 3: Company info (optional)
  - Step 4: Submit + loading state
- [ ] Build result display: `DecisionBadge` + `AgentBreakdown` cards post-submission
- [ ] Implement `DeviceInput` capture (IP via API call, fingerprint via string hash of UA + screen)

**Acceptance Criteria:**
- Complete form submission flow works end-to-end with real backend
- Decision result (APPROVE/REVIEW/REJECT) displayed with agent breakdown
- Biometric signals are captured and sent with submission

---

### 🟦 Phase 6: Analyst Dashboard (Hour 28–34)

**Frontend Dev:**

- [ ] Implement `RiskMeter.tsx` gauge component
- [ ] Implement `DecisionBadge.tsx`
- [ ] Implement `AgentBreakdown.tsx`
- [ ] Implement `FlagList.tsx` (list of risk flag tags)
- [ ] Build `DashboardPage.tsx`:
  - Stats cards: Total / Approved / Review / Rejected counts
  - Average risk score gauge
  - Recent decisions table (last 10)
  - Link to Review Queue
- [ ] Build `ReviewQueuePage.tsx`:
  - List of REVIEW applications with expandable rows
  - Each row: name, email, overall risk, decision badge, timestamp
  - Expanded view: agent breakdown cards + AI explanation

**Acceptance Criteria:**
- Dashboard loads and displays seeded stats
- Review Queue lists REVIEW applications
- Expanding a row shows full risk breakdown

---

### 🟦 Phase 7: Human-in-the-Loop (Hour 34–38)

**Frontend Dev:**

- [ ] Implement `AnalystOverride.tsx` form component
- [ ] Wire override form into `ReviewQueuePage` — appears in expanded row
- [ ] On override submit: call `POST /api/v1/analyst/override` and refresh queue
- [ ] Show success/error toast notification

**Backend Dev:**

- [ ] Implement `POST /api/v1/analyst/override` fully (update application status, save to DB)
- [ ] Implement `GET /api/v1/analyst/stats` with real DB aggregation

**Acceptance Criteria:**
- Analyst can submit CONFIRMED_FRAUD / CLEARED / NEEDS_MORE_INFO
- Row disappears from REVIEW queue after CONFIRMED_FRAUD or CLEARED
- Dashboard stats update after override

---

### 🟦 Phase 8: Integration & Edge Cases (Hour 38–44)

**All developers:**

- [ ] End-to-end test: Submit 3 different profiles (clean / suspicious / synthetic) — verify correct decisions
- [ ] Test guardrail: Temporarily break Qwen API key → verify REVIEW fallback works
- [ ] Test with missing fields: Submit form without company info, without images — verify no crashes
- [ ] Verify Docker Compose runs cleanly from fresh clone:
  ```bash
  docker-compose down -v
  docker-compose up --build
  docker-compose exec backend python seed_demo.py
  ```
- [ ] Fix any CORS issues between frontend and backend
- [ ] Verify Nginx proxy routes `/api` correctly in Docker

---

### 🟦 Phase 9: Polish & Demo Prep (Hour 44–48)

**Frontend Dev:**
- [ ] Responsive design check (mobile-friendly for demo)
- [ ] Loading spinners on all async operations
- [ ] Error state displays (API down message)
- [ ] Visual polish: colors, spacing, consistent typography

**All developers:**
- [ ] Deploy to Alibaba ECS (see `docs/DOCKER_SETUP.md` §8)
- [ ] Verify public URL works
- [ ] Record 3-minute demo walkthrough video (optional)
- [ ] Prepare pitch script
- [ ] Final README check

---

## 3. Git Workflow

### Branch Strategy

```
main
├── feature/backend-db-setup
├── feature/backend-agents
├── feature/backend-api-routes
├── feature/frontend-onboarding
├── feature/frontend-dashboard
└── feature/docker-setup
```

### Commit Convention

```
feat(backend): implement identity risk agent with Qwen integration
fix(frontend): correct biometric entropy calculation
docs: add API contract to DEVELOPMENT_GUIDE.md
chore(docker): add health check to backend service
```

### Pull Request Checklist
- [ ] Feature works locally with Docker Compose
- [ ] No hardcoded secrets or API keys
- [ ] TypeScript errors resolved (`npm run build` passes)
- [ ] Python syntax valid (`python -m py_compile <file>`)
- [ ] Brief description of change in PR body

---

## 4. Complete API Contract

### Base URL
- **Local:** `http://localhost:8000`
- **Docker (via Nginx proxy):** `http://localhost/api` (proxy strips `/api` prefix... or keep it, configure Nginx accordingly)

All endpoints return `Content-Type: application/json`.

---

### `GET /health`

**Description:** Service health check.

**Response 200:**
```json
{
  "status": "ok",
  "service": "payshield-ai"
}
```

---

### `POST /api/v1/applications/submit`

**Description:** Submit onboarding application for full risk assessment.

**Request Body:**
```json
{
  "user": {
    "full_name": "string (required)",
    "email": "string (required)",
    "phone": "string (required)",
    "date_of_birth": "YYYY-MM-DD (optional)",
    "address": "string (optional)",
    "country": "string (optional)",
    "ktp_number": "string (optional, 16-digit NIK)"
  },
  "company": {
    "name": "string (optional)",
    "registration_number": "string (optional)"
  },
  "biometrics": {
    "typing_cadence_ms": [120, 95, 130, 88],
    "mouse_entropy_score": 0.72,
    "session_duration_sec": 145,
    "navigation_path": ["home", "register", "identity", "submit"]
  },
  "device": {
    "ip_address": "string (required)",
    "user_agent": "string (required)",
    "device_fingerprint": "string (required)"
  },
  "ktp_image_base64": "string (optional, base64-encoded image)",
  "selfie_image_base64": "string (optional, base64-encoded image)"
}
```

**Response 200:**
```json
{
  "application_id": "uuid-string",
  "identity_risk": 0.0,
  "behavior_risk": 0.0,
  "network_risk": 0.0,
  "overall_risk": 0.0,
  "decision": "APPROVE | REVIEW | REJECT",
  "confidence": 0.0,
  "explanation": "string",
  "agent_details": {
    "identity": {
      "score": 0.0,
      "flags": ["FLAG_NAME"]
    },
    "behavioral": {
      "score": 0.0,
      "flags": []
    },
    "network": {
      "score": 0.0,
      "flags": []
    }
  }
}
```

**Response 422:** Pydantic validation error (missing required fields).

---

### `GET /api/v1/decisions/review-queue`

**Description:** Fetch all applications currently in REVIEW state.

**Response 200:**
```json
[
  {
    "application_id": "uuid-string",
    "full_name": "string",
    "email": "string",
    "overall_risk": 0.0,
    "identity_risk": 0.0,
    "behavior_risk": 0.0,
    "network_risk": 0.0,
    "confidence": 0.0,
    "decision": "REVIEW",
    "explanation": "string",
    "flags": ["FLAG_NAME"],
    "created_at": "ISO-8601 timestamp"
  }
]
```

---

### `GET /api/v1/decisions/{application_id}`

**Description:** Fetch full decision details for a specific application.

**Path Param:** `application_id` — UUID of the application.

**Response 200:** Same as review queue item but for a single application.

**Response 404:**
```json
{ "detail": "Application not found" }
```

---

### `POST /api/v1/analyst/override`

**Description:** Submit human analyst override decision.

**Request Body:**
```json
{
  "application_id": "uuid-string (required)",
  "human_decision": "CONFIRMED_FRAUD | CLEARED | NEEDS_MORE_INFO (required)",
  "analyst_note": "string (optional)",
  "analyst_id": "string (optional, default: analyst_001)"
}
```

**Response 200:**
```json
{
  "message": "Override recorded successfully",
  "application_id": "uuid-string",
  "new_status": "REJECT | APPROVE | REVIEW"
}
```

**Status mapping:**
- `CONFIRMED_FRAUD` → application.status = `REJECT`
- `CLEARED` → application.status = `APPROVE`
- `NEEDS_MORE_INFO` → application.status = `REVIEW` (remains in queue)

---

### `GET /api/v1/analyst/stats`

**Description:** Fetch dashboard statistics.

**Response 200:**
```json
{
  "total_applications": 0,
  "approved": 0,
  "review": 0,
  "rejected": 0,
  "override_count": 0,
  "avg_risk_score": 0.0
}
```

---

## 5. Development Checklist

### Backend
- [ ] `GET /health` returns 200
- [ ] `POST /submit` with valid payload returns `ApplicationResponse`
- [ ] `POST /submit` with missing required fields returns 422
- [ ] All 3 decision types can be generated
- [ ] Guardrail triggers on invalid AI output
- [ ] DB persists applications and decisions
- [ ] Review queue returns only `REVIEW` status apps
- [ ] Analyst override updates application status
- [ ] Seed script runs without errors
- [ ] No hardcoded API keys (all from `.env`)

### Frontend
- [ ] Onboarding form submits successfully
- [ ] Biometric signals captured during form fill
- [ ] Result page shows decision badge + agent breakdown
- [ ] Dashboard loads stats
- [ ] Review queue lists REVIEW applications
- [ ] Analyst override form submits and refreshes queue
- [ ] No TypeScript compile errors (`npm run build`)
- [ ] Runs in Docker via Nginx

### Infrastructure
- [ ] `docker-compose up --build` starts all services cleanly
- [ ] Frontend served at port 80
- [ ] Backend accessible at port 8000
- [ ] Nginx proxy routes `/api` to backend
- [ ] `.env.example` documents all required variables

---

## 6. Testing Strategy

### Manual Test Scenarios

**Scenario A — Legitimate User (expected: APPROVE)**
```json
{
  "user": { "full_name": "Budi Santoso", "email": "budi@gmail.com",
            "phone": "+6281234567890", "ktp_number": "3174052505900001" },
  "biometrics": { "typing_cadence_ms": [95, 110, 88, 130, 102],
                  "mouse_entropy_score": 0.78, "session_duration_sec": 180 },
  "device": { "ip_address": "103.10.20.30", "user_agent": "Chrome/120",
              "device_fingerprint": "fp_clean_001" }
}
```

**Scenario B — Suspicious (expected: REVIEW)**
```json
{
  "user": { "full_name": "Anon User", "email": "temp@mailinator.com",
            "phone": "+6289999999999", "ktp_number": "0000000000000000" },
  "biometrics": { "typing_cadence_ms": [3, 2, 4, 3],
                  "mouse_entropy_score": 0.15, "session_duration_sec": 8 },
  "device": { "ip_address": "185.220.101.50", "user_agent": "python-requests",
              "device_fingerprint": "fp_suspicious_002" }
}
```

**Scenario C — Full Synthetic Identity (expected: REJECT)**
- Submit Scenario B's profile 3 more times to build phone/device reuse signal
- Then submit a variant — network extractor should return high `shared_phone_account_count`

### Quick curl test
```bash
# Submit test application
curl -s -X POST http://localhost:8000/api/v1/applications/submit \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/clean_user.json | python3 -m json.tool
```

### Automated Tests (optional, for extra points)

```bash
# backend/tests/test_policy_layer.py
import pytest
from app.guardrails.policy_layer import PolicyLayer

def test_approve_low_risk():
    layer = PolicyLayer()
    result = layer.enforce({
        "identity_risk": 0.1, "behavior_risk": 0.05, "network_risk": 0.02,
        "overall_risk": 0.07, "decision": "APPROVE", "confidence": 0.9,
        "explanation": "Test", "flags": []
    })
    assert result["decision"] == "APPROVE"

def test_review_on_low_confidence():
    layer = PolicyLayer()
    result = layer.enforce({
        "identity_risk": 0.1, "behavior_risk": 0.05, "network_risk": 0.02,
        "overall_risk": 0.07, "decision": "APPROVE", "confidence": 0.3,
        "explanation": "Test", "flags": []
    })
    assert result["decision"] == "REVIEW"  # Low confidence forces REVIEW

def test_reject_high_risk():
    layer = PolicyLayer()
    result = layer.enforce({
        "identity_risk": 0.9, "behavior_risk": 0.85, "network_risk": 0.88,
        "overall_risk": 0.88, "decision": "REJECT", "confidence": 0.92,
        "explanation": "Test", "flags": ["KTP_MISMATCH"]
    })
    assert result["decision"] == "REJECT"

def test_guardrail_invalid_score():
    layer = PolicyLayer()
    result = layer.enforce({
        "identity_risk": 1.5,  # Invalid: > 1.0
        "behavior_risk": 0.5, "network_risk": 0.5,
        "overall_risk": 0.5, "decision": "REVIEW", "confidence": 0.6,
        "explanation": "Test", "flags": []
    })
    assert result["guardrail_triggered"] == True
```

Run tests:
```bash
cd backend
pip install pytest
pytest tests/
```

---

## 7. Demo Preparation

### Demo Flow (3 minutes)

**Minute 1 — Problem & Solution (Slides)**
- Show the fraud landscape stat (synthetic identity fraud is $X billion)
- One slide: "Traditional systems vs PayShield AI"
- One slide: Architecture overview diagram

**Minute 2 — Live Demo**

1. Open `http://<ecs-ip>` (Onboarding form)
2. Fill in a **suspicious profile** (disposable email, unusual name)
3. Submit — show loading state (AI thinking)
4. Show result: `REVIEW` decision with agent breakdown cards and risk meters
5. Navigate to **Analyst Dashboard**
6. Open **Review Queue** — show the queued application
7. Expand it — show AI explanation, flags, confidence score
8. Click **Confirm Fraud** → decision updated
9. Show dashboard stats updated

**Minute 3 — Architecture & Innovation Points**
- Show `PROMPT_ENGINEERING.md` screenshot — "5-layer hallucination guard"
- Show guardrail code — "AI never makes final decisions alone"
- Emphasize: built in 48 hours on Alibaba Cloud with Qwen

### Backup Plan (if live API fails)
- Pre-seed database with demo data: `python seed_demo.py`
- Have screenshots/recording of working demo
- Dashboard with seeded stats will show even without Qwen API

### Key Talking Points
- **AI Utilization (30%):** Meta-agent orchestration, not just one LLM call — three specialized agents + orchestrator
- **Hallucination Safety:** Show the guardrail layer code — "fintech cannot afford hallucinated rejections"
- **Human-in-the-Loop:** "REVIEW state prevents financial exclusion — AI recommends, humans decide"
- **Alibaba Cloud:** Qwen via Model Studio, deployable on single ECS under $20
