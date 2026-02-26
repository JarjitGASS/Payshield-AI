# 🏗 PayShield AI — System Architecture

## Table of Contents
1. [High-Level Overview](#1-high-level-overview)
2. [Component Breakdown](#2-component-breakdown)
3. [Agentic Risk Engine Design](#3-agentic-risk-engine-design)
4. [Data Flow — Full Request Lifecycle](#4-data-flow--full-request-lifecycle)
5. [Hallucination Reduction Architecture](#5-hallucination-reduction-architecture)
6. [Human-in-the-Loop Design](#6-human-in-the-loop-design)
7. [Feature Extraction Layer](#7-feature-extraction-layer)
8. [Policy Guardrail Layer](#8-policy-guardrail-layer)
9. [Security Considerations](#9-security-considerations)

---

## 1. High-Level Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
│                                                                      │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐  │
│  │     Onboarding UI            │  │    Analyst Dashboard         │  │
│  │  (Registration Form +        │  │  (Risk Queue + Override UI)  │  │
│  │   Biometric Capture)         │  │                              │  │
│  └──────────────┬───────────────┘  └───────────────┬──────────────┘  │
│                 │ REST / JSON                       │ REST / JSON     │
└─────────────────┼───────────────────────────────────┼────────────────┘
                  │                                   │
┌─────────────────▼───────────────────────────────────▼────────────────┐
│                         BACKEND LAYER (FastAPI)                       │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    API Router Layer                             │  │
│  │  POST /applications/submit  GET /decisions/*  POST /analyst/*  │  │
│  └────────────────────────────┬────────────────────────────────────┘  │
│                               │                                       │
│  ┌────────────────────────────▼────────────────────────────────────┐  │
│  │                Feature Extraction Layer                         │  │
│  │  ┌───────────────┐  ┌────────────────┐  ┌───────────────────┐  │  │
│  │  │   Identity    │  │  Behavioral    │  │     Network       │  │  │
│  │  │   Extractor   │  │   Extractor    │  │    Extractor      │  │  │
│  │  └───────┬───────┘  └───────┬────────┘  └─────────┬─────────┘  │  │
│  └──────────┼──────────────────┼───────────────────────┼──────────┘  │
│             │                  │                       │              │
│  ┌──────────▼──────────────────▼───────────────────────▼──────────┐  │
│  │                  Qwen Agentic Risk Engine                       │  │
│  │                                                                 │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │  │
│  │  │  Identity Risk   │  │  Behavioral      │  │  Synthetic   │  │  │
│  │  │     Agent        │  │  Anomaly Agent   │  │  Network     │  │  │
│  │  │                  │  │                  │  │  Agent       │  │  │
│  │  │ • KTP match      │  │ • Typing cadence │  │ • Phone reuse│  │  │
│  │  │ • Face similarity│  │ • Mouse entropy  │  │ • Device reuse│ │  │
│  │  │ • Email age      │  │ • Session timing │  │ • Rapid create│ │  │
│  │  │ • Geo-IP mismatch│  │ • Nav consistency│  │ • Cross-merch │  │  │
│  │  │ • Name entropy   │  │                  │  │               │  │  │
│  │  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘  │  │
│  │           │                     │                    │          │  │
│  │  ┌────────▼─────────────────────▼────────────────────▼───────┐  │  │
│  │  │              Meta-Agent Orchestrator (Qwen LLM)           │  │  │
│  │  │  • Consumes all three agent outputs                       │  │  │
│  │  │  • Resolves conflicting signals                           │  │  │
│  │  │  • Produces final structured JSON decision                │  │  │
│  │  └──────────────────────────────┬────────────────────────────┘  │  │
│  └─────────────────────────────────┼─────────────────────────────── ┘  │
│                                    │                                    │
│  ┌─────────────────────────────────▼──────────────────────────────┐   │
│  │                  Policy Guardrail Layer                         │   │
│  │  • JSON schema validation      • Score range enforcement       │   │
│  │  • Decision consistency check  • Confidence threshold          │   │
│  │  • Fallback to REVIEW on fail  • Final APPROVE/REVIEW/REJECT   │   │
│  └─────────────────────────────────┬──────────────────────────────┘   │
└────────────────────────────────────┼──────────────────────────────────┘
                                     │
┌────────────────────────────────────▼──────────────────────────────────┐
│                         DATABASE LAYER                                 │
│                     SQLite / PostgreSQL                                │
│  applications  •  risk_decisions  •  analyst_overrides  •  audit_log  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Breakdown

### Frontend (React + Vite + TypeScript)

| Component | Responsibility |
|---|---|
| `OnboardingPage` | Collects user registration data, initiates biometric capture |
| `BiometricCapture` | Records keystroke timing and mouse movement entropy |
| `DashboardPage` | Analyst overview: risk statistics, pending reviews |
| `ReviewQueuePage` | Lists all REVIEW-state applications for analyst action |
| `RiskMeter` | Visual gauge for overall and per-agent risk scores |
| `AgentBreakdown` | Cards showing identity / behavioral / network sub-scores |
| `DecisionBadge` | Color-coded APPROVE (green) / REVIEW (yellow) / REJECT (red) |
| `AnalystOverride` | Form for analyst to confirm fraud, clear, or escalate |
| `useBiometrics` hook | Collects typing cadence intervals and mouse entropy |
| `useRiskAssessment` hook | Wraps API calls to the backend risk submission endpoint |

### Backend (FastAPI + Python)

| Module | Responsibility |
|---|---|
| `api/routes/applications.py` | POST endpoint for application submission |
| `api/routes/decisions.py` | GET endpoints for decision retrieval and review queue |
| `api/routes/analyst.py` | POST endpoint for human override submission |
| `extractors/identity_extractor.py` | Normalize and score identity signals |
| `extractors/behavioral_extractor.py` | Compute behavioral entropy and anomaly scores |
| `extractors/network_extractor.py` | Query DB for shared signals across accounts |
| `agents/identity_agent.py` | Build identity agent context + invoke Qwen |
| `agents/behavioral_agent.py` | Build behavioral agent context + invoke Qwen |
| `agents/network_agent.py` | Build network agent context + invoke Qwen |
| `agents/meta_orchestrator.py` | Combine all agent outputs + final Qwen reasoning |
| `guardrails/policy_layer.py` | Validate AI output + enforce policy decisions |
| `models/schemas.py` | Pydantic request/response schemas |
| `models/db_models.py` | SQLAlchemy ORM table definitions |
| `db/database.py` | DB engine + session factory |

---

## 3. Agentic Risk Engine Design

### Design Pattern: Simulated Multi-Agent via Single Orchestrated LLM

To stay within the 48-hour scope and $20 Alibaba Cloud budget, the three agents are **logical agents** rather than separate deployments. Each agent is implemented as:

1. A **deterministic feature extractor** (pure Python)
2. A **structured Qwen LLM call** with agent-specific system prompt
3. A **validated output schema** per agent

The meta-orchestrator then makes **one final Qwen call** combining all three agent outputs.

```
Application Input
       │
       ├──▶ [Identity Extractor] ──▶ [Identity Agent Qwen Call] ──▶ identity_result
       │
       ├──▶ [Behavioral Extractor] ──▶ [Behavioral Agent Qwen Call] ──▶ behavior_result
       │
       └──▶ [Network Extractor] ──▶ [Network Agent Qwen Call] ──▶ network_result
                                              │
                                    [Meta-Orchestrator Qwen Call]
                                    (all 3 results as context)
                                              │
                                    Final Structured Decision
```

### Identity Risk Agent

**Input signals:**
- `ktp_match_score` (0–1): How well form data matches KTP document fields
- `face_similarity_score` (0–1): KTP photo vs selfie comparison (vision model)
- `email_age_days` (int): Age of email domain registration
- `phone_reuse_count` (int): Number of accounts using same phone
- `geo_ip_mismatch` (bool): Declared address vs IP geolocation mismatch
- `name_entropy` (float): Entropy of full name string (catches random-generated names)
- `entity_sentiment_score` (float): Public sentiment score for user/company

**Output schema:**
```json
{
  "identity_risk": 0.0,
  "flags": ["string"],
  "explanation": "string",
  "confidence": 0.0
}
```

### Behavioral Anomaly Agent

**Input signals:**
- `typing_cadence_variance` (float): Std deviation of inter-keystroke intervals (ms)
- `mouse_entropy_score` (float): Shannon entropy of mouse movement vectors
- `session_duration_sec` (int): Total registration session time
- `login_hour` (int): Hour of day (0–23), checked against typical patterns
- `navigation_consistency_score` (float): Deviation from expected navigation flow

**Output schema:**
```json
{
  "behavior_risk": 0.0,
  "flags": ["string"],
  "explanation": "string",
  "confidence": 0.0
}
```

### Synthetic Network Agent

**Input signals:**
- `shared_phone_account_count` (int): Other accounts with same phone number
- `shared_device_account_count` (int): Other accounts with same device fingerprint
- `shared_ip_account_count` (int): Other accounts from same IP in last 30 days
- `account_age_hours` (float): Time since account creation
- `cross_merchant_reuse` (bool): Device/phone seen across different merchant applications

**Output schema:**
```json
{
  "network_risk": 0.0,
  "flags": ["string"],
  "explanation": "string",
  "confidence": 0.0
}
```

### Meta-Agent Orchestrator

**Input:** All three agent outputs combined.

**Final output schema:**
```json
{
  "identity_risk": 0.0,
  "behavior_risk": 0.0,
  "network_risk": 0.0,
  "overall_risk": 0.0,
  "decision": "APPROVE | REVIEW | REJECT",
  "confidence": 0.0,
  "explanation": "string",
  "flags": ["string"]
}
```

The meta-agent uses **weighted averaging** as a fallback:
```
overall_risk = (identity_risk × 0.45) + (behavior_risk × 0.25) + (network_risk × 0.30)
```

---

## 4. Data Flow — Full Request Lifecycle

```
Step 1: User submits onboarding form
        └─▶ React captures: form data + biometric signals + device info
        └─▶ POST /api/v1/applications/submit

Step 2: Backend receives and validates request
        └─▶ Pydantic schema validation
        └─▶ Application saved to DB with status=PENDING

Step 3: Feature Extraction (parallel)
        ├─▶ IdentityExtractor.extract(user_data, ktp_data) → identity_features
        ├─▶ BehavioralExtractor.extract(biometrics) → behavioral_features
        └─▶ NetworkExtractor.extract(device, phone, db) → network_features

Step 4: Agent Analysis (sequential Qwen calls)
        ├─▶ IdentityAgent.analyze(identity_features) → identity_result
        ├─▶ BehavioralAgent.analyze(behavioral_features) → behavior_result
        └─▶ NetworkAgent.analyze(network_features) → network_result

Step 5: Meta-Orchestration
        └─▶ MetaOrchestrator.decide(identity_result, behavior_result, network_result)
            └─▶ Qwen produces final structured JSON decision

Step 6: Guardrail Validation
        └─▶ Validate JSON structure
        └─▶ Validate score ranges (0.0–1.0)
        └─▶ Validate decision vs overall_risk consistency
        └─▶ Validate confidence threshold
        └─▶ On failure: downgrade to REVIEW, log incident

Step 7: Policy Enforcement
        └─▶ overall_risk < 0.3  AND confidence >= 0.5 → APPROVE
        └─▶ overall_risk 0.3–0.7 OR confidence < 0.5 → REVIEW
        └─▶ overall_risk > 0.7  AND confidence >= 0.5 → REJECT

Step 8: Decision persisted to DB
        └─▶ risk_decisions table updated
        └─▶ If REVIEW: added to review queue

Step 9: Response returned to client
        └─▶ Full decision JSON with agent breakdown

Step 10 (async, REVIEW only): Analyst reviews
        └─▶ Dashboard displays signals + AI explanation
        └─▶ Analyst submits override via POST /api/v1/analyst/override
        └─▶ Decision updated, feedback stored for calibration
```

---

## 5. Hallucination Reduction Architecture

### Layer 1: Evidence-Bounded Prompting
All prompts include the explicit instruction:
> "Only reason from the signals provided. Do not invent, assume, or reference information not in the input. If a signal is missing, treat it as unknown and state so."

### Layer 2: Structured JSON Output Enforcement
```python
# After every Qwen call:
try:
    result = json.loads(response.content)
    validate_schema(result, AGENT_SCHEMA)
except (json.JSONDecodeError, ValidationError):
    # Retry once with stricter prompt
    # If retry fails: return default REVIEW decision
    return fallback_review_decision()
```

### Layer 3: Deterministic Model Configuration
```python
qwen_params = {
    "model": "qwen-max",
    "temperature": 0.2,    # Low randomness
    "top_p": 0.8,
    "max_tokens": 512,     # Prevent runaway output
    "response_format": {"type": "json_object"}
}
```

### Layer 4: Guardrail Validation
```python
def validate_ai_output(result: dict) -> bool:
    # Score range check
    for field in ["identity_risk", "behavior_risk", "network_risk", "overall_risk"]:
        if not (0.0 <= result[field] <= 1.0):
            return False
    # Decision consistency check
    if result["overall_risk"] > 0.7 and result["decision"] == "APPROVE":
        return False
    if result["overall_risk"] < 0.3 and result["decision"] == "REJECT":
        return False
    # Confidence threshold
    if result["confidence"] < 0.0 or result["confidence"] > 1.0:
        return False
    return True
```

### Layer 5: AI as Advisory Only
The LLM **recommends** — the **policy layer enforces**:

| Overall Risk | Confidence | Final Decision |
|---|---|---|
| < 0.3 | ≥ 0.5 | APPROVE |
| 0.3 – 0.7 | any | REVIEW |
| > 0.7 | ≥ 0.5 | REJECT |
| any | < 0.5 | REVIEW |
| AI output invalid | — | REVIEW |

---

## 6. Human-in-the-Loop Design

### REVIEW State Lifecycle

```
AI Decision: REVIEW
       │
       ▼
Added to Review Queue (DB status = REVIEW)
       │
       ▼
Analyst Dashboard displays:
  • Risk scores breakdown (identity / behavioral / network)
  • All signal flags
  • AI explanation text
  • Confidence score
  • Application raw data
       │
       ▼
Analyst makes decision:
  ├─▶ CONFIRMED_FRAUD  → REJECT + fraud label stored
  ├─▶ CLEARED         → APPROVE + false positive label stored
  └─▶ NEEDS_MORE_INFO → Remain REVIEW + note added
       │
       ▼
Feedback stored in analyst_overrides table
  {
    "application_id": "uuid",
    "ai_decision": "REVIEW",
    "ai_overall_risk": 0.52,
    "human_decision": "CONFIRMED_FRAUD",
    "analyst_id": "analyst_001",
    "analyst_note": "Phone reused across 6 accounts. Synthetic cluster.",
    "timestamp": "2026-02-26T10:00:00Z"
  }
       │
       ▼
Used for threshold calibration (post-hackathon)
```

### Confidence-Based Auto-Escalation
Any AI output with `confidence < 0.5` is automatically routed to REVIEW, regardless of risk score. This prevents low-certainty decisions from being applied automatically.

---

## 7. Feature Extraction Layer

### Identity Feature Extraction

```python
class IdentityExtractor:
    def extract(self, user_data: UserInput, ktp_data: KTPData) -> IdentityFeatures:
        return IdentityFeatures(
            ktp_match_score=self._compare_ktp_fields(user_data, ktp_data),
            face_similarity_score=self._face_compare(ktp_data.photo, user_data.selfie),
            email_age_days=self._lookup_email_age(user_data.email),
            phone_reuse_count=self._db_phone_count(user_data.phone),
            geo_ip_mismatch=self._geo_ip_check(user_data.address, user_data.ip),
            name_entropy=self._name_entropy(user_data.full_name),
            entity_sentiment_score=self._entity_scrape(user_data.full_name, company)
        )
```

**KTP Match Score**: Levenshtein distance comparison between form fields and KTP OCR output (name, DOB, address, NIK number). Returns a normalized similarity score (0–1).

**Face Similarity**: Uses Qwen-VL (vision model) to compare KTP photo vs selfie, or falls back to a simple base64 pixel hash diff if vision is unavailable.

**Entity Scrape** (optional, controlled by `ENABLE_ENTITY_SCRAPE` env flag): Queries DuckDuckGo API for user/company mentions and returns a simple presence-and-sentiment score.

### Behavioral Feature Extraction

```python
class BehavioralExtractor:
    def extract(self, biometrics: BiometricInput) -> BehavioralFeatures:
        cadence_list = biometrics.typing_cadence_ms
        return BehavioralFeatures(
            typing_cadence_variance=statistics.stdev(cadence_list) if len(cadence_list) > 1 else 0,
            mouse_entropy_score=biometrics.mouse_entropy_score,
            session_duration_sec=biometrics.session_duration_sec,
            login_hour=datetime.now().hour,
            navigation_consistency_score=self._nav_score(biometrics.navigation_path)
        )
```

**Typing Cadence Variance**: Standard deviation of inter-keystroke intervals. Bots tend toward very low variance (uniform timing). Suspiciously high values may indicate scripted paste operations.

**Mouse Entropy**: Shannon entropy of movement vectors computed client-side and sent as a pre-computed score. Range 0–1 where values near 0 indicate robotic linear movement.

**Navigation Consistency**: Expected navigation path is `["home", "register", "identity", "document", "submit"]`. Deviation from this path is scored as anomalous.

### Network Feature Extraction

```python
class NetworkExtractor:
    def extract(self, device: DeviceInput, phone: str, db: Session) -> NetworkFeatures:
        return NetworkFeatures(
            shared_phone_count=self._count_phone(phone, db),
            shared_device_count=self._count_device(device.fingerprint, db),
            shared_ip_count=self._count_ip_30d(device.ip_address, db),
            account_age_hours=self._account_age(db),
            cross_merchant_reuse=self._cross_merchant(device.fingerprint, db)
        )
```

---

## 8. Policy Guardrail Layer

The policy layer is **deterministic** — it never calls the AI. It acts as the final authority.

```python
class PolicyLayer:
    APPROVE_THRESHOLD = 0.3
    REJECT_THRESHOLD = 0.7
    MIN_CONFIDENCE = 0.5

    def enforce(self, ai_output: RiskDecision) -> RiskDecision:
        # Guardrail validation first
        if not self._validate(ai_output):
            ai_output.decision = "REVIEW"
            ai_output.explanation += " [GUARDRAIL: Output failed validation, escalated to REVIEW]"
            return ai_output

        # Policy enforcement
        risk = ai_output.overall_risk
        conf = ai_output.confidence

        if conf < self.MIN_CONFIDENCE:
            ai_output.decision = "REVIEW"
        elif risk < self.APPROVE_THRESHOLD:
            ai_output.decision = "APPROVE"
        elif risk > self.REJECT_THRESHOLD:
            ai_output.decision = "REJECT"
        else:
            ai_output.decision = "REVIEW"

        return ai_output
```

---

## 9. Security Considerations

| Concern | Mitigation |
|---|---|
| API key exposure | Keys only in `.env`, never committed to git |
| KTP image storage | Base64 images stored encrypted at rest, deleted after 24h |
| SQL injection | All DB queries via SQLAlchemy ORM (parameterized) |
| Input validation | Pydantic schemas on all endpoints |
| Rate limiting | FastAPI rate limiter middleware on submission endpoint |
| CORS | Strict CORS to `FRONTEND_URL` only |
| Analyst auth | JWT-based authentication for analyst routes |
| AI output trust | AI output NEVER written to DB unvalidated — always passes guardrail first |
