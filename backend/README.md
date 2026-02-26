# 🐍 PayShield AI — Backend Guide

## Stack
- **Framework:** FastAPI (Python 3.11+)
- **AI:** Qwen via Alibaba Cloud Model Studio (OpenAI-compatible SDK)
- **Database:** SQLite (dev) / PostgreSQL (prod) via SQLAlchemy
- **Validation:** Pydantic v2

---

## Table of Contents
1. [Project Setup](#1-project-setup)
2. [Directory Structure](#2-directory-structure)
3. [Dependencies](#3-dependencies)
4. [Database Models](#4-database-models)
5. [Pydantic Schemas](#5-pydantic-schemas)
6. [Feature Extractors](#6-feature-extractors)
7. [Agent Implementations](#7-agent-implementations)
8. [Meta-Orchestrator](#8-meta-orchestrator)
9. [Guardrail & Policy Layer](#9-guardrail--policy-layer)
10. [API Routes Reference](#10-api-routes-reference)
11. [Running the Backend](#11-running-the-backend)

---

## 1. Project Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env   # fill in QWEN_API_KEY
uvicorn main:app --reload --port 8000
```

Access Swagger UI at: http://localhost:8000/docs

---

## 2. Directory Structure

```
backend/
├── Dockerfile
├── requirements.txt
├── main.py
└── app/
    ├── api/
    │   └── routes/
    │       ├── applications.py
    │       ├── decisions.py
    │       └── analyst.py
    ├── agents/
    │   ├── identity_agent.py
    │   ├── behavioral_agent.py
    │   ├── network_agent.py
    │   └── meta_orchestrator.py
    ├── extractors/
    │   ├── identity_extractor.py
    │   ├── behavioral_extractor.py
    │   └── network_extractor.py
    ├── guardrails/
    │   └── policy_layer.py
    ├── models/
    │   ├── schemas.py
    │   └── db_models.py
    └── db/
        └── database.py
```

---

## 3. Dependencies

**`requirements.txt`**
```
fastapi==0.111.0
uvicorn[standard]==0.30.1
pydantic==2.7.1
sqlalchemy==2.0.30
alembic==1.13.1
openai==1.30.5          # Alibaba Model Studio uses OpenAI-compatible API
python-dotenv==1.0.1
httpx==0.27.0
python-multipart==0.0.9
pillow==10.3.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
slowapi==0.1.9
```

---

## 4. Database Models

**`app/models/db_models.py`**

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

def new_uuid():
    return str(uuid.uuid4())

class Application(Base):
    __tablename__ = "applications"

    id = Column(String, primary_key=True, default=new_uuid)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    date_of_birth = Column(String)
    address = Column(String)
    country = Column(String)
    ktp_number = Column(String)
    company_name = Column(String)
    company_reg_number = Column(String)
    ip_address = Column(String)
    device_fingerprint = Column(String)
    user_agent = Column(String)
    status = Column(String, default="PENDING")  # PENDING | APPROVE | REVIEW | REJECT
    created_at = Column(DateTime, default=datetime.utcnow)


class RiskDecision(Base):
    __tablename__ = "risk_decisions"

    id = Column(String, primary_key=True, default=new_uuid)
    application_id = Column(String, nullable=False)
    identity_risk = Column(Float)
    behavior_risk = Column(Float)
    network_risk = Column(Float)
    overall_risk = Column(Float)
    decision = Column(String)           # APPROVE | REVIEW | REJECT
    confidence = Column(Float)
    explanation = Column(Text)
    agent_flags = Column(Text)          # JSON string
    guardrail_triggered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnalystOverride(Base):
    __tablename__ = "analyst_overrides"

    id = Column(String, primary_key=True, default=new_uuid)
    application_id = Column(String, nullable=False)
    ai_decision = Column(String)
    ai_overall_risk = Column(Float)
    human_decision = Column(String)     # CONFIRMED_FRAUD | CLEARED | NEEDS_MORE_INFO
    analyst_id = Column(String)
    analyst_note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=new_uuid)
    application_id = Column(String)
    event = Column(String)              # SUBMITTED | ASSESSED | OVERRIDDEN | GUARDRAIL_TRIGGERED
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 5. Pydantic Schemas

**`app/models/schemas.py`**

```python
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date

# ── Inbound ──────────────────────────────────────────────────────────

class UserInput(BaseModel):
    full_name: str
    email: str
    phone: str
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    ktp_number: Optional[str] = None

class CompanyInput(BaseModel):
    name: Optional[str] = None
    registration_number: Optional[str] = None

class BiometricInput(BaseModel):
    typing_cadence_ms: List[float] = []   # inter-keystroke intervals
    mouse_entropy_score: float = 0.5
    session_duration_sec: int = 60
    navigation_path: List[str] = []

class DeviceInput(BaseModel):
    ip_address: str
    user_agent: str
    device_fingerprint: str

class ApplicationSubmitRequest(BaseModel):
    user: UserInput
    company: Optional[CompanyInput] = None
    biometrics: Optional[BiometricInput] = None
    device: DeviceInput
    ktp_image_base64: Optional[str] = None
    selfie_image_base64: Optional[str] = None

# ── Outbound ─────────────────────────────────────────────────────────

class AgentDetail(BaseModel):
    score: float
    flags: List[str]
    explanation: str

class ApplicationResponse(BaseModel):
    application_id: str
    identity_risk: float
    behavior_risk: float
    network_risk: float
    overall_risk: float
    decision: str
    confidence: float
    explanation: str
    agent_details: dict

class ReviewQueueItem(BaseModel):
    application_id: str
    full_name: str
    email: str
    overall_risk: float
    identity_risk: float
    behavior_risk: float
    network_risk: float
    confidence: float
    decision: str
    explanation: str
    flags: List[str]
    created_at: str

class AnalystOverrideRequest(BaseModel):
    application_id: str
    human_decision: str             # CONFIRMED_FRAUD | CLEARED | NEEDS_MORE_INFO
    analyst_note: Optional[str] = ""
    analyst_id: Optional[str] = "analyst_001"
```

---

## 6. Feature Extractors

### `app/extractors/identity_extractor.py`

```python
import math
import statistics
from difflib import SequenceMatcher
from app.models.schemas import UserInput, BiometricInput, DeviceInput
from sqlalchemy.orm import Session

class IdentityExtractor:
    def extract(self, user: UserInput, ktp_image_b64: str, selfie_b64: str, db: Session) -> dict:
        return {
            "ktp_match_score": self._ktp_field_match(user),
            "face_similarity_score": self._face_score(ktp_image_b64, selfie_b64),
            "email_age_days": self._email_age(user.email),
            "phone_reuse_count": self._phone_reuse(user.phone, db),
            "geo_ip_mismatch": False,  # Extend with GeoIP library in production
            "name_entropy": self._name_entropy(user.full_name),
            "entity_sentiment_score": 0.7  # Default; enable scraper with env flag
        }

    def _ktp_field_match(self, user: UserInput) -> float:
        # Compare form-submitted name vs KTP name via string similarity
        # In a real implementation, OCR the KTP image and compare fields
        # For MVP: if KTP number is present and non-empty, score is higher
        if user.ktp_number and len(user.ktp_number) == 16:
            return 0.85  # NIK is 16 digits — basic format check
        return 0.4

    def _face_score(self, ktp_b64: str, selfie_b64: str) -> float:
        # For MVP: return 0.8 if both images are provided
        # In production: call Qwen-VL or a dedicated face comparison service
        if ktp_b64 and selfie_b64:
            return 0.80
        return 0.5  # Unknown, neutral score

    def _email_age(self, email: str) -> int:
        # Heuristic: disposable/temporary email domains return low age
        disposable_domains = ["guerrillamail.com", "mailinator.com", "tempmail.com", "10minutemail.com"]
        domain = email.split("@")[-1] if "@" in email else ""
        if domain in disposable_domains:
            return 0
        return 365  # Default: assume established email

    def _phone_reuse(self, phone: str, db: Session) -> int:
        from app.models.db_models import Application
        count = db.query(Application).filter(Application.phone == phone).count()
        return count

    def _name_entropy(self, name: str) -> float:
        # Shannon entropy of character distribution
        # Low entropy (< 2.0) → very repetitive → suspicious
        if not name:
            return 0.0
        name_lower = name.lower().replace(" ", "")
        freq = {c: name_lower.count(c) / len(name_lower) for c in set(name_lower)}
        return -sum(p * math.log2(p) for p in freq.values())
```

### `app/extractors/behavioral_extractor.py`

```python
import statistics
import math
from datetime import datetime
from app.models.schemas import BiometricInput

EXPECTED_NAV_PATH = ["home", "register", "identity", "document", "submit"]

class BehavioralExtractor:
    def extract(self, biometrics: BiometricInput) -> dict:
        cadence = biometrics.typing_cadence_ms
        return {
            "typing_cadence_variance": statistics.stdev(cadence) if len(cadence) > 1 else 0.0,
            "mouse_entropy_score": biometrics.mouse_entropy_score,
            "session_duration_sec": biometrics.session_duration_sec,
            "login_hour": datetime.utcnow().hour,
            "navigation_consistency_score": self._nav_score(biometrics.navigation_path)
        }

    def _nav_score(self, path: list) -> float:
        if not path:
            return 0.5  # Unknown
        matches = sum(1 for a, b in zip(path, EXPECTED_NAV_PATH) if a == b)
        return matches / max(len(EXPECTED_NAV_PATH), len(path))
```

### `app/extractors/network_extractor.py`

```python
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.db_models import Application
from app.models.schemas import DeviceInput

class NetworkExtractor:
    def extract(self, device: DeviceInput, phone: str, db: Session) -> dict:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        return {
            "shared_phone_account_count": self._count_phone(phone, db),
            "shared_device_account_count": self._count_device(device.device_fingerprint, db),
            "shared_ip_account_count": self._count_ip(device.ip_address, db, thirty_days_ago),
            "account_age_hours": 0.5,  # New account — set post-creation
            "cross_merchant_reuse": False  # Extend with merchant-level tracking
        }

    def _count_phone(self, phone: str, db: Session) -> int:
        return db.query(Application).filter(Application.phone == phone).count()

    def _count_device(self, fingerprint: str, db: Session) -> int:
        return db.query(Application).filter(
            Application.device_fingerprint == fingerprint
        ).count()

    def _count_ip(self, ip: str, db: Session, since: datetime) -> int:
        return db.query(Application).filter(
            Application.ip_address == ip,
            Application.created_at >= since
        ).count()
```

---

## 7. Agent Implementations

### `app/agents/identity_agent.py`

```python
import json
import os
from openai import OpenAI
from app.models.schemas import UserInput

IDENTITY_SYSTEM_PROMPT = """You are the Identity Risk Agent for PayShield AI, a financial fraud detection system.

Your role is to analyze identity legitimacy signals and produce a structured risk assessment.

RULES:
- Only reason from the signals provided in the input.
- Do not invent, assume, or reference any information not explicitly given.
- If a signal is missing or unknown, treat it as neutral (0.5 for scores, unknown for booleans).
- Output ONLY valid JSON matching the required schema. No prose, no markdown.

OUTPUT SCHEMA:
{
  "identity_risk": <float 0.0-1.0>,
  "flags": [<list of string flag names>],
  "explanation": <string, max 200 chars, referencing only provided signals>,
  "confidence": <float 0.0-1.0>
}

FLAG NAMES (use only these):
KTP_MISMATCH, FACE_MISMATCH, DISPOSABLE_EMAIL, PHONE_REUSE,
GEO_IP_MISMATCH, LOW_NAME_ENTROPY, NEGATIVE_ENTITY_SENTIMENT, LOW_ENTITY_PRESENCE
"""

class IdentityAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("QWEN_API_KEY"),
            base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        )

    def analyze(self, features: dict) -> dict:
        user_content = f"""
Analyze the following identity signals and return a risk assessment:

- ktp_match_score: {features.get('ktp_match_score')} (1.0 = perfect match, 0.0 = complete mismatch)
- face_similarity_score: {features.get('face_similarity_score')} (1.0 = same person, 0.0 = different)
- email_age_days: {features.get('email_age_days')} (0 = disposable/new)
- phone_reuse_count: {features.get('phone_reuse_count')} (number of other accounts using this phone)
- geo_ip_mismatch: {features.get('geo_ip_mismatch')} (true = declared address does not match IP location)
- name_entropy: {features.get('name_entropy')} (< 2.0 = suspiciously low-entropy name)
- entity_sentiment_score: {features.get('entity_sentiment_score')} (1.0 = positive public presence, 0.0 = none/negative)

Return ONLY the JSON object as specified.
"""
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("QWEN_MODEL", "qwen-max"),
                messages=[
                    {"role": "system", "content": IDENTITY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2,
                top_p=0.8,
                max_tokens=512,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            # Fallback: return conservative neutral assessment
            return {
                "identity_risk": 0.5,
                "flags": [],
                "explanation": f"Identity agent unavailable: {str(e)[:50]}",
                "confidence": 0.3
            }
```

> **Note:** `behavioral_agent.py` and `network_agent.py` follow the identical pattern — different system prompt, different input signals, same output structure. See [`docs/PROMPT_ENGINEERING.md`](../docs/PROMPT_ENGINEERING.md) for all three prompt templates.

---

## 8. Meta-Orchestrator

**`app/agents/meta_orchestrator.py`**

```python
import json
import os
from openai import OpenAI

META_SYSTEM_PROMPT = """You are the Meta-Agent Orchestrator for PayShield AI.

You receive risk assessments from three specialized agents:
1. Identity Risk Agent
2. Behavioral Anomaly Agent
3. Synthetic Network Agent

Your job is to:
- Synthesize all three assessments into one final decision
- Resolve conflicting signals by weighing evidence
- Produce a final structured risk decision

RULES:
- Only reason from the agent outputs provided.
- Do not invent signals not present in the input.
- Output ONLY valid JSON. No prose, no markdown.
- The "decision" field is a RECOMMENDATION only — a policy layer will enforce the final action.

OUTPUT SCHEMA:
{
  "identity_risk": <float 0.0-1.0>,
  "behavior_risk": <float 0.0-1.0>,
  "network_risk": <float 0.0-1.0>,
  "overall_risk": <float 0.0-1.0, weighted synthesis>,
  "decision": <"APPROVE" | "REVIEW" | "REJECT">,
  "confidence": <float 0.0-1.0>,
  "explanation": <string, max 400 chars>,
  "flags": [<all flags from all agents combined>]
}

Risk thresholds for your recommendation:
- overall_risk < 0.3 → APPROVE
- overall_risk 0.3-0.7 → REVIEW
- overall_risk > 0.7 → REJECT
- If any agent confidence < 0.4 → prefer REVIEW
"""

class MetaOrchestrator:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("QWEN_API_KEY"),
            base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        )

    def decide(self, identity_result: dict, behavior_result: dict, network_result: dict) -> dict:
        user_content = f"""
Synthesize the following three agent assessments into a final risk decision:

IDENTITY RISK AGENT OUTPUT:
{json.dumps(identity_result, indent=2)}

BEHAVIORAL ANOMALY AGENT OUTPUT:
{json.dumps(behavior_result, indent=2)}

SYNTHETIC NETWORK AGENT OUTPUT:
{json.dumps(network_result, indent=2)}

Provide the final synthesized JSON decision.
"""
        try:
            response = self.client.chat.completions.create(
                model=os.getenv("QWEN_MODEL", "qwen-max"),
                messages=[
                    {"role": "system", "content": META_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2,
                top_p=0.8,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            # Deterministic fallback: weighted average, force REVIEW
            overall = (
                identity_result.get("identity_risk", 0.5) * 0.45 +
                behavior_result.get("behavior_risk", 0.5) * 0.25 +
                network_result.get("network_risk", 0.5) * 0.30
            )
            return {
                "identity_risk": identity_result.get("identity_risk", 0.5),
                "behavior_risk": behavior_result.get("behavior_risk", 0.5),
                "network_risk": network_result.get("network_risk", 0.5),
                "overall_risk": round(overall, 3),
                "decision": "REVIEW",
                "confidence": 0.4,
                "explanation": f"Meta-orchestrator unavailable ({str(e)[:50]}). Fallback: escalated to REVIEW.",
                "flags": []
            }
```

---

## 9. Guardrail & Policy Layer

**`app/guardrails/policy_layer.py`**

```python
from typing import Optional

APPROVE_THRESHOLD = 0.3
REJECT_THRESHOLD = 0.7
MIN_CONFIDENCE = 0.5

REQUIRED_FIELDS = [
    "identity_risk", "behavior_risk", "network_risk",
    "overall_risk", "decision", "confidence", "explanation"
]
VALID_DECISIONS = {"APPROVE", "REVIEW", "REJECT"}

class PolicyLayer:
    def enforce(self, ai_output: dict) -> dict:
        """
        Validates AI output and enforces deterministic policy.
        Returns the (possibly modified) decision dict.
        """
        guardrail_triggered = False

        # --- Structural Validation ---
        for field in REQUIRED_FIELDS:
            if field not in ai_output:
                ai_output[field] = self._default(field)
                guardrail_triggered = True

        # --- Score Range Validation ---
        for score_field in ["identity_risk", "behavior_risk", "network_risk", "overall_risk", "confidence"]:
            val = ai_output.get(score_field, 0.5)
            if not isinstance(val, (int, float)) or not (0.0 <= float(val) <= 1.0):
                ai_output[score_field] = 0.5
                guardrail_triggered = True

        # --- Decision Validity ---
        if ai_output.get("decision") not in VALID_DECISIONS:
            ai_output["decision"] = "REVIEW"
            guardrail_triggered = True

        # --- Decision Consistency ---
        risk = ai_output["overall_risk"]
        decision = ai_output["decision"]
        if risk > REJECT_THRESHOLD and decision == "APPROVE":
            ai_output["decision"] = "REVIEW"
            guardrail_triggered = True
        if risk < APPROVE_THRESHOLD and decision == "REJECT":
            ai_output["decision"] = "REVIEW"
            guardrail_triggered = True

        # --- Policy Enforcement (deterministic override) ---
        conf = ai_output["confidence"]
        if conf < MIN_CONFIDENCE:
            ai_output["decision"] = "REVIEW"
        elif risk < APPROVE_THRESHOLD:
            ai_output["decision"] = "APPROVE"
        elif risk > REJECT_THRESHOLD:
            ai_output["decision"] = "REJECT"
        else:
            ai_output["decision"] = "REVIEW"

        if guardrail_triggered:
            ai_output["explanation"] = (
                ai_output.get("explanation", "") +
                " [GUARDRAIL: Output anomaly detected, policy enforced]"
            )

        ai_output["guardrail_triggered"] = guardrail_triggered
        return ai_output

    def _default(self, field: str):
        defaults = {
            "identity_risk": 0.5, "behavior_risk": 0.5, "network_risk": 0.5,
            "overall_risk": 0.5, "decision": "REVIEW",
            "confidence": 0.4, "explanation": "Missing field - defaulted by guardrail.",
            "flags": []
        }
        return defaults.get(field, None)
```

---

## 10. API Routes Reference

### `POST /api/v1/applications/submit`

Full pipeline: extract features → run agents → meta-orchestrate → guardrail → persist → respond.

```python
# app/api/routes/applications.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.schemas import ApplicationSubmitRequest, ApplicationResponse
from app.extractors.identity_extractor import IdentityExtractor
from app.extractors.behavioral_extractor import BehavioralExtractor
from app.extractors.network_extractor import NetworkExtractor
from app.agents.identity_agent import IdentityAgent
from app.agents.behavioral_agent import BehavioralAgent
from app.agents.network_agent import NetworkAgent
from app.agents.meta_orchestrator import MetaOrchestrator
from app.guardrails.policy_layer import PolicyLayer
from app.models.db_models import Application, RiskDecision
import json

router = APIRouter(prefix="/api/v1/applications", tags=["Applications"])

@router.post("/submit", response_model=ApplicationResponse)
def submit_application(payload: ApplicationSubmitRequest, db: Session = Depends(get_db)):
    # 1. Persist application
    app_record = Application(
        full_name=payload.user.full_name,
        email=payload.user.email,
        phone=payload.user.phone,
        date_of_birth=payload.user.date_of_birth,
        address=payload.user.address,
        country=payload.user.country,
        ktp_number=payload.user.ktp_number,
        company_name=payload.company.name if payload.company else None,
        ip_address=payload.device.ip_address,
        device_fingerprint=payload.device.device_fingerprint,
        user_agent=payload.device.user_agent,
        status="PENDING"
    )
    db.add(app_record)
    db.commit()
    db.refresh(app_record)

    # 2. Extract features
    id_features = IdentityExtractor().extract(
        payload.user, payload.ktp_image_base64, payload.selfie_image_base64, db
    )
    beh_features = BehavioralExtractor().extract(payload.biometrics or BiometricInput())
    net_features = NetworkExtractor().extract(payload.device, payload.user.phone, db)

    # 3. Run agents
    id_result = IdentityAgent().analyze(id_features)
    beh_result = BehavioralAgent().analyze(beh_features)
    net_result = NetworkAgent().analyze(net_features)

    # 4. Meta-orchestrate
    final = MetaOrchestrator().decide(id_result, beh_result, net_result)

    # 5. Guardrail + policy enforcement
    final = PolicyLayer().enforce(final)

    # 6. Persist decision
    decision_record = RiskDecision(
        application_id=app_record.id,
        identity_risk=final["identity_risk"],
        behavior_risk=final["behavior_risk"],
        network_risk=final["network_risk"],
        overall_risk=final["overall_risk"],
        decision=final["decision"],
        confidence=final["confidence"],
        explanation=final["explanation"],
        agent_flags=json.dumps(final.get("flags", [])),
        guardrail_triggered=final.get("guardrail_triggered", False)
    )
    db.add(decision_record)
    app_record.status = final["decision"]
    db.commit()

    return ApplicationResponse(
        application_id=app_record.id,
        identity_risk=final["identity_risk"],
        behavior_risk=final["behavior_risk"],
        network_risk=final["network_risk"],
        overall_risk=final["overall_risk"],
        decision=final["decision"],
        confidence=final["confidence"],
        explanation=final["explanation"],
        agent_details={
            "identity": {"score": id_result.get("identity_risk"), "flags": id_result.get("flags", [])},
            "behavioral": {"score": beh_result.get("behavior_risk"), "flags": beh_result.get("flags", [])},
            "network": {"score": net_result.get("network_risk"), "flags": net_result.get("flags", [])}
        }
    )
```

### `GET /api/v1/decisions/review-queue`
Returns all applications with `decision = REVIEW`.

### `GET /api/v1/decisions/{application_id}`
Returns full decision detail for one application.

### `POST /api/v1/analyst/override`
Saves human analyst override. Updates application status.

### `GET /api/v1/analyst/stats`
Returns dashboard statistics: total applications, breakdown by decision, override counts.

---

## 11. Running the Backend

```bash
# Development
uvicorn main:app --reload --port 8000

# Production (inside Docker)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Swagger UI:** http://localhost:8000/docs  
**ReDoc:** http://localhost:8000/redoc
