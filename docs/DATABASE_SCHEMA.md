# 🗄 PayShield AI — Database Schema

## Overview

PayShield AI uses **SQLite** for local development and **PostgreSQL** for production. The schema is managed via **SQLAlchemy ORM** with optional **Alembic** migrations.

All tables use UUID primary keys (string representation).

---

## Table of Contents
1. [Entity Relationship Overview](#1-entity-relationship-overview)
2. [Table Definitions](#2-table-definitions)
3. [SQLAlchemy ORM Setup](#3-sqlalchemy-orm-setup)
4. [Indexes & Performance Notes](#4-indexes--performance-notes)
5. [Seed Data for Demo](#5-seed-data-for-demo)
6. [Migration Commands](#6-migration-commands)

---

## 1. Entity Relationship Overview

```
┌─────────────────────┐
│     applications    │
│─────────────────────│
│ id (PK)             │◄──────────────────────────────────┐
│ full_name           │                                   │
│ email               │                                   │
│ phone               │                                   │
│ date_of_birth       │                                   │
│ address             │                                   │
│ country             │                                   │
│ ktp_number          │                                   │
│ company_name        │                                   │
│ company_reg_number  │                                   │
│ ip_address          │                                   │
│ device_fingerprint  │                                   │
│ user_agent          │                                   │
│ status              │ ── PENDING|APPROVE|REVIEW|REJECT  │
│ created_at          │                                   │
└─────────────────────┘                                   │
                                                          │
┌─────────────────────┐                                   │
│   risk_decisions    │                                   │
│─────────────────────│                                   │
│ id (PK)             │                                   │
│ application_id (FK) │───────────────────────────────────┤
│ identity_risk       │                                   │
│ behavior_risk       │                                   │
│ network_risk        │                                   │
│ overall_risk        │                                   │
│ decision            │ ── APPROVE|REVIEW|REJECT          │
│ confidence          │                                   │
│ explanation         │                                   │
│ agent_flags         │ ── JSON string                    │
│ guardrail_triggered │                                   │
│ created_at          │                                   │
└─────────────────────┘                                   │
                                                          │
┌─────────────────────┐                                   │
│  analyst_overrides  │                                   │
│─────────────────────│                                   │
│ id (PK)             │                                   │
│ application_id (FK) │───────────────────────────────────┤
│ ai_decision         │                                   │
│ ai_overall_risk     │                                   │
│ human_decision      │ ── CONFIRMED_FRAUD|CLEARED|...    │
│ analyst_id          │                                   │
│ analyst_note        │                                   │
│ created_at          │                                   │
└─────────────────────┘                                   │
                                                          │
┌─────────────────────┐                                   │
│     audit_log       │                                   │
│─────────────────────│                                   │
│ id (PK)             │                                   │
│ application_id (FK) │───────────────────────────────────┘
│ event               │ ── SUBMITTED|ASSESSED|OVERRIDDEN|...
│ detail              │
│ created_at          │
└─────────────────────┘
```

---

## 2. Table Definitions

### `applications`

Stores raw onboarding submission data from users.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PK | UUID v4 |
| `full_name` | VARCHAR(255) | NOT NULL | User's full legal name |
| `email` | VARCHAR(255) | NOT NULL | User's email address |
| `phone` | VARCHAR(50) | NOT NULL | Phone number (with country code) |
| `date_of_birth` | VARCHAR(20) | NULLABLE | YYYY-MM-DD format |
| `address` | TEXT | NULLABLE | Full residential address |
| `country` | VARCHAR(100) | NULLABLE | ISO 3166-1 alpha-2 or full name |
| `ktp_number` | VARCHAR(30) | NULLABLE | Indonesian NIK (16 digits) |
| `company_name` | VARCHAR(255) | NULLABLE | Registered company name |
| `company_reg_number` | VARCHAR(100) | NULLABLE | Company registration number |
| `ip_address` | VARCHAR(50) | NULLABLE | IPv4 or IPv6 address at submission time |
| `device_fingerprint` | VARCHAR(255) | NULLABLE | Browser/device fingerprint hash |
| `user_agent` | TEXT | NULLABLE | HTTP User-Agent string |
| `status` | VARCHAR(20) | DEFAULT 'PENDING' | PENDING / APPROVE / REVIEW / REJECT |
| `created_at` | DATETIME | DEFAULT NOW | UTC timestamp |

**Notes:**
- `ktp_number` is not unique — duplicate KTP numbers are a fraud signal tracked via query
- `device_fingerprint` should be generated client-side using a library like FingerprintJS
- KTP and selfie images are **NOT** stored in the database — processed in memory and discarded

---

### `risk_decisions`

Stores AI risk assessment output for each application.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PK | UUID v4 |
| `application_id` | VARCHAR(36) | NOT NULL, FK → applications.id | Links to the application |
| `identity_risk` | FLOAT | NULLABLE | Identity Risk Agent output (0.0–1.0) |
| `behavior_risk` | FLOAT | NULLABLE | Behavioral Anomaly Agent output (0.0–1.0) |
| `network_risk` | FLOAT | NULLABLE | Synthetic Network Agent output (0.0–1.0) |
| `overall_risk` | FLOAT | NULLABLE | Meta-orchestrator weighted synthesis (0.0–1.0) |
| `decision` | VARCHAR(20) | NOT NULL | APPROVE / REVIEW / REJECT |
| `confidence` | FLOAT | NULLABLE | AI confidence in assessment (0.0–1.0) |
| `explanation` | TEXT | NULLABLE | AI-generated explanation string |
| `agent_flags` | TEXT | NULLABLE | JSON array string of all triggered flags |
| `guardrail_triggered` | BOOLEAN | DEFAULT FALSE | True if guardrail layer modified AI output |
| `created_at` | DATETIME | DEFAULT NOW | UTC timestamp |

---

### `analyst_overrides`

Stores human analyst override decisions for REVIEW-state applications.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PK | UUID v4 |
| `application_id` | VARCHAR(36) | NOT NULL, FK → applications.id | Links to the application |
| `ai_decision` | VARCHAR(20) | NULLABLE | The AI's original decision before override |
| `ai_overall_risk` | FLOAT | NULLABLE | The AI's overall_risk score at time of override |
| `human_decision` | VARCHAR(30) | NOT NULL | CONFIRMED_FRAUD / CLEARED / NEEDS_MORE_INFO |
| `analyst_id` | VARCHAR(100) | NULLABLE | Identifier of the analyst who reviewed |
| `analyst_note` | TEXT | NULLABLE | Free-text investigation notes |
| `created_at` | DATETIME | DEFAULT NOW | UTC timestamp |

**`human_decision` values:**
- `CONFIRMED_FRAUD` — Analyst confirms this is a fraudulent application
- `CLEARED` — Analyst confirms this is a legitimate application (false positive)
- `NEEDS_MORE_INFO` — Analyst requires additional information before deciding

---

### `audit_log`

Immutable event log for compliance and debugging.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | PK | UUID v4 |
| `application_id` | VARCHAR(36) | NULLABLE | Associated application (if applicable) |
| `event` | VARCHAR(50) | NOT NULL | Event type (see below) |
| `detail` | TEXT | NULLABLE | JSON-serialized event detail |
| `created_at` | DATETIME | DEFAULT NOW | UTC timestamp |

**`event` values:**
- `SUBMITTED` — Application received from user
- `ASSESSED` — AI risk assessment completed
- `GUARDRAIL_TRIGGERED` — Policy guardrail modified AI output
- `OVERRIDDEN` — Human analyst submitted override decision
- `AGENT_FAILURE` — An AI agent call failed (fallback used)

---

## 3. SQLAlchemy ORM Setup

**`app/db/database.py`**

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.db_models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./payshield.db")

# SQLite needs check_same_thread=False for FastAPI async
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """FastAPI dependency: yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**`main.py` — Call `init_db()` on startup:**

```python
from fastapi import FastAPI
from app.db.database import init_db
from app.api.routes import applications, decisions, analyst

app = FastAPI(title="PayShield AI API", version="1.0.0")

@app.on_event("startup")
def startup():
    init_db()

app.include_router(applications.router)
app.include_router(decisions.router)
app.include_router(analyst.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "payshield-ai"}
```

---

## 4. Indexes & Performance Notes

For the hackathon demo (SQLite, small dataset), explicit indexes are not required. For production PostgreSQL:

```sql
-- Speed up fraud cluster lookups
CREATE INDEX idx_applications_phone ON applications(phone);
CREATE INDEX idx_applications_device ON applications(device_fingerprint);
CREATE INDEX idx_applications_ip ON applications(ip_address);
CREATE INDEX idx_applications_status ON applications(status);

-- Speed up decision queries
CREATE INDEX idx_risk_decisions_application_id ON risk_decisions(application_id);
CREATE INDEX idx_risk_decisions_decision ON risk_decisions(decision);

-- Speed up override queries
CREATE INDEX idx_overrides_application_id ON analyst_overrides(application_id);

-- Speed up audit queries
CREATE INDEX idx_audit_application_id ON audit_log(application_id);
CREATE INDEX idx_audit_event ON audit_log(event);
```

---

## 5. Seed Data for Demo

Use this script to populate the database with realistic demo data for the hackathon presentation.

**`backend/seed_demo.py`**

```python
"""
Run: python seed_demo.py
Populates DB with demo applications covering all three decision types.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import SessionLocal, init_db
from app.models.db_models import Application, RiskDecision
import uuid
from datetime import datetime, timedelta
import random

init_db()
db = SessionLocal()

DEMO_APPS = [
    # Clean application → APPROVE
    {
        "app": dict(full_name="Budi Santoso", email="budi.santoso@gmail.com", phone="+6281234567890",
                    date_of_birth="1990-05-15", address="Jl. Sudirman No. 10, Jakarta", country="Indonesia",
                    ktp_number="3174052505900001", company_name="PT Santoso Digital", ip_address="103.10.20.30",
                    device_fingerprint="fp_abc123xyz", user_agent="Mozilla/5.0 Chrome/120", status="APPROVE"),
        "decision": dict(identity_risk=0.12, behavior_risk=0.08, network_risk=0.05, overall_risk=0.09,
                         decision="APPROVE", confidence=0.92,
                         explanation="All identity signals consistent. Normal behavioral patterns. No network reuse detected.",
                         agent_flags="[]", guardrail_triggered=False)
    },
    # Suspicious → REVIEW
    {
        "app": dict(full_name="Anom Wibowo", email="temp123@mailinator.com", phone="+6289876543210",
                    date_of_birth="1985-11-22", address="Jl. Gatot Subroto 50, Bandung", country="Indonesia",
                    ktp_number="3273225211850001", company_name=None, ip_address="185.220.101.50",
                    device_fingerprint="fp_def456uvw", user_agent="Mozilla/5.0 Firefox/115", status="REVIEW"),
        "decision": dict(identity_risk=0.55, behavior_risk=0.30, network_risk=0.25, overall_risk=0.41,
                         decision="REVIEW", confidence=0.62,
                         explanation="Disposable email detected. Geo-IP mismatch. Moderate identity and behavioral risk signals.",
                         agent_flags='["DISPOSABLE_EMAIL", "GEO_IP_MISMATCH"]', guardrail_triggered=False)
    },
    # Synthetic identity → REJECT
    {
        "app": dict(full_name="Xqz Prtklmn", email="xqzprtklmn99@protonmail.com", phone="+6281111111111",
                    date_of_birth="1999-01-01", address="Jl. Unknown 999, Surabaya", country="Indonesia",
                    ktp_number="3578010101990001", company_name="CV Maju Cepat", ip_address="45.66.77.88",
                    device_fingerprint="fp_ghi789rst", user_agent="python-requests/2.28", status="REJECT"),
        "decision": dict(identity_risk=0.88, behavior_risk=0.91, network_risk=0.87, overall_risk=0.89,
                         decision="REJECT", confidence=0.95,
                         explanation="KTP mismatch, face mismatch. Bot-like typing cadence (variance 0.3ms). Phone reused across 7 accounts. Strong synthetic identity indicators.",
                         agent_flags='["KTP_MISMATCH", "FACE_MISMATCH", "BOT_TYPING_CADENCE", "PHONE_CLUSTER", "SYNTHETIC_FARM_INDICATOR"]',
                         guardrail_triggered=False)
    },
]

for item in DEMO_APPS:
    app_id = str(uuid.uuid4())
    app = Application(id=app_id, **item["app"],
                      created_at=datetime.utcnow() - timedelta(minutes=random.randint(5, 60)))
    db.add(app)
    decision = RiskDecision(id=str(uuid.uuid4()), application_id=app_id, **item["decision"],
                            created_at=app.created_at)
    db.add(decision)

db.commit()
db.close()
print("✅ Demo data seeded successfully.")
```

---

## 6. Migration Commands

### SQLite (Dev — automatic table creation)
```bash
# Tables are auto-created on app startup via init_db()
# No migration needed for SQLite dev workflow
```

### PostgreSQL with Alembic (Production)

```bash
# Initialize alembic (run once)
cd backend
alembic init alembic

# Edit alembic/env.py to import your Base and DATABASE_URL
# Then generate first migration:
alembic revision --autogenerate -m "initial schema"

# Apply migration:
alembic upgrade head

# Rollback one step:
alembic downgrade -1
```

**`alembic/env.py` key lines:**
```python
from app.models.db_models import Base
from app.db.database import DATABASE_URL

config.set_main_option("sqlalchemy.url", DATABASE_URL)
target_metadata = Base.metadata
```
