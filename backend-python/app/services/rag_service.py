"""
RAG Service — Fetch historical agent results from Postgres for prompt augmentation,
and store new results after successful agent runs.

Agents call these functions to ground their reasoning in real past decisions (RAG pattern).
"""
from contextlib import contextmanager
from sqlalchemy.orm import Session
from model.rag_history import AgentHistory, OrchestratorHistory
from database.database import SessionLocal
from typing import List, Optional
import json


@contextmanager
def _get_db():
    """Context manager that always closes the session, even on error."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
# FETCH: Retrieval for RAG prompt augmentation
# ─────────────────────────────────────────────────────────────

def fetch_agent_history(
    agent_step: str,
    limit: int = 3,
    min_confidence: float = 0.5,
) -> str:
    """
    Retrieve recent successful agent results for a given agent step.
    Returns formatted string to inject into agent prompts.
    """
    with _get_db() as db:
        try:
            rows = (
                db.query(AgentHistory)
                .filter(AgentHistory.agent_step == agent_step)
                .filter(AgentHistory.confidence >= min_confidence)
                .order_by(AgentHistory.created_at.desc())
                .limit(limit)
                .all()
            )
            if not rows:
                return "No historical cases found for this agent."

            context_lines = []
            for row in rows:
                context_lines.append(
                    f"- Session {row.session_id}: risk={row.risk:.2f}, "
                    f"confidence={row.confidence:.2f}, flags={row.flags}, "
                    f"explanation={row.explanation}"
                )
            return "Recent historical assessments from this agent:\n" + "\n".join(context_lines)
        except Exception as e:
            return f"RAG fetch failed: {e}"


def fetch_orchestrator_history(
    limit: int = 5,
    decision_filter: Optional[str] = None,
) -> str:
    """
    Retrieve recent orchestrator decisions for RAG prompt augmentation.
    Optionally filter by decision type (APPROVE/REVIEW/REJECT).
    """
    with _get_db() as db:
        try:
            query = db.query(OrchestratorHistory).order_by(OrchestratorHistory.created_at.desc())
            if decision_filter:
                query = query.filter(OrchestratorHistory.decision == decision_filter)
            rows = query.limit(limit).all()

            if not rows:
                return "No historical orchestrator decisions found."

            context_lines = []
            for row in rows:
                override = ""
                if row.human_override_decision:
                    override = f" [HUMAN OVERRIDE: {row.human_override_decision} — {row.human_override_note}]"
                context_lines.append(
                    f"- Session {row.session_id}: overall_risk={row.overall_risk:.2f}, "
                    f"decision={row.decision}, confidence={row.confidence:.2f}, "
                    f"flags={row.flags}{override}"
                )
            return "Recent orchestrator decisions:\n" + "\n".join(context_lines)
        except Exception as e:
            return f"RAG orchestrator fetch failed: {e}"

def fetch_similar_flags_history(flags: List[str], limit: int = 3) -> str:
    """
    Retrieve historical cases that share the same flags as the current assessment.
    Useful for finding patterns across similar fraud signals.
    """
    with _get_db() as db:
        try:
            rows = (
                db.query(OrchestratorHistory)
                .order_by(OrchestratorHistory.created_at.desc())
                .limit(50)
                .all()
            )
            # Filter by shared flags in Python (JSON column)
            matched = []
            for row in rows:
                stored_flags = row.flags or []
                overlap = set(flags) & set(stored_flags)
                if overlap:
                    matched.append((row, overlap))
            matched = matched[:limit]

            if not matched:
                return "No historical cases with matching flags found."

            context_lines = []
            for row, overlap in matched:
                context_lines.append(
                    f"- Session {row.session_id}: shared_flags={list(overlap)}, "
                    f"decision={row.decision}, overall_risk={row.overall_risk:.2f}"
                )
            return "Historical cases with similar flags:\n" + "\n".join(context_lines)
        except Exception as e:
            return f"RAG similar-flags fetch failed: {e}"

def store_agent_result(
    session_id: str,
    agent_step: str,
    input_features: dict,
    risk: float,
    confidence: float,
    flags: list,
    explanation: str,
) -> None:
    """Store an individual agent result into the RAG history table."""
    with _get_db() as db:
        try:
            record = AgentHistory(
                session_id=session_id,
                agent_step=agent_step,
                input_features=input_features,
                risk=risk,
                confidence=confidence,
                flags=flags,
                explanation=explanation,
            )
            db.add(record)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[RAG] Failed to store agent result: {e}")


def store_orchestrator_result(
    session_id: str,
    identity_risk: float,
    behavior_risk: float,
    network_risk: float,
    overall_risk: float,
    decision: str,
    confidence: float,
    explanation: str,
    flags: list,
) -> None:
    """Store an orchestrator result into the RAG history table."""
    with _get_db() as db:
        try:
            record = OrchestratorHistory(
                session_id=session_id,
                identity_risk=identity_risk,
                behavior_risk=behavior_risk,
                network_risk=network_risk,
                overall_risk=overall_risk,
                decision=decision,
                confidence=confidence,
                explanation=explanation,
                flags=flags,
            )
            db.add(record)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[RAG] Failed to store orchestrator result: {e}")

def store_human_review(
    session_id: str,
    override_decision: str,
    override_note: str,
) -> dict:
    """
    Store a human analyst's review for a given session.

    Updates the existing OrchestratorHistory row with the analyst's
    override decision and note. Returns the updated record as a dict,
    or raises ValueError / RuntimeError on failure.
    """
    with _get_db() as db:
        try:
            record = (
                db.query(OrchestratorHistory)
                .filter(OrchestratorHistory.session_id == session_id)
                .first()
            )
            if not record:
                raise ValueError(f"Session {session_id} not found in orchestrator history")

            if record.human_override_decision is not None:
                raise ValueError(
                    f"Session {session_id} has already been reviewed "
                    f"(override={record.human_override_decision})"
                )

            record.human_override_decision = override_decision
            record.human_override_note = override_note
            db.commit()
            db.refresh(record)

            return {
                "session_id": record.session_id,
                "original_decision": record.decision,
                "override_decision": record.human_override_decision,
                "override_note": record.human_override_note,
                "overall_risk": record.overall_risk,
            }
        except ValueError:
            raise
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"Failed to store human review: {e}")

def fetch_human_review_context(limit: int = 5) -> str:
    """
    Retrieve recent HITL-reviewed sessions for RAG prompt injection.

    Returns a formatted string containing analyst overrides so agents
    can learn from human corrections and calibrate their reasoning.
    Only returns sessions where an analyst has actually submitted a review.
    """
    with _get_db() as db:
        try:
            rows = (
                db.query(OrchestratorHistory)
                .filter(OrchestratorHistory.human_override_decision.isnot(None))
                .order_by(OrchestratorHistory.updated_at.desc())
                .limit(limit)
                .all()
            )
            if not rows:
                return ""

            context_lines = []
            for row in rows:
                was_correct = row.human_override_decision == row.decision
                verdict = "CONFIRMED" if was_correct else "CORRECTED"
                context_lines.append(
                    f"- Session {row.session_id}: "
                    f"AI_decision={row.decision}, "
                    f"analyst_override={row.human_override_decision} ({verdict}), "
                    f"overall_risk={row.overall_risk:.2f}, "
                    f"flags={row.flags}, "
                    f"analyst_note=\"{row.human_override_note}\""
                )
            return (
                "Recent human analyst reviews (use these to calibrate your decisions):\n"
                + "\n".join(context_lines)
            )
        except Exception as e:
            return f"HITL RAG fetch failed: {e}"


def fetch_pending_reviews(limit: int = 20) -> list:
    """
    Retrieve sessions with REVIEW decision that have NOT yet been
    reviewed by a human analyst. Used by the pending-reviews endpoint.
    """
    with _get_db() as db:
        try:
            rows = (
                db.query(OrchestratorHistory)
                .filter(OrchestratorHistory.decision == "REVIEW")
                .filter(OrchestratorHistory.human_override_decision.is_(None))
                .order_by(OrchestratorHistory.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "session_id": row.session_id,
                    "overall_risk": row.overall_risk,
                    "identity_risk": row.identity_risk,
                    "behavior_risk": row.behavior_risk,
                    "network_risk": row.network_risk,
                    "confidence": row.confidence,
                    "decision": row.decision,
                    "flags": row.flags,
                    "explanation": row.explanation,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ]
        except Exception as e:
            print(f"[RAG] Failed to fetch pending reviews: {e}")
            return []
