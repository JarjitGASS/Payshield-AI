"""
Adaptive Threshold Service — replaces hardcoded guardrail thresholds
with data-driven dynamic thresholds computed from historical orchestrator
decisions stored in the RAG history table.

Strategy:
  - Compute a moving average of past overall_risk scores grouped by decision.
  - Use historical distribution to determine adaptive boundaries.
  - Fall back to sensible defaults when insufficient data.
"""
from typing import Dict, Optional
from database.database import SessionLocal
from model.rag_history import OrchestratorHistory
from sqlalchemy import func

# ─────────────────────────────────────────────────────────────
# Defaults (used when < MIN_SAMPLES exist)
# ─────────────────────────────────────────────────────────────
DEFAULT_APPROVE_THRESHOLD = 0.3
DEFAULT_REJECT_THRESHOLD = 0.7
DEFAULT_MIN_CONFIDENCE = 0.5
MIN_SAMPLES = 10  # minimum rows needed before switching to adaptive


def get_adaptive_thresholds() -> Dict[str, float]:
    """
    Compute adaptive thresholds from historical orchestrator decisions.

    Logic:
      1. Fetch mean overall_risk per decision category (APPROVE, REJECT, REVIEW).
      2. Set APPROVE_THRESHOLD = midpoint between mean(APPROVE) and mean(REVIEW).
      3. Set REJECT_THRESHOLD  = midpoint between mean(REVIEW) and mean(REJECT).
      4. Set MIN_CONFIDENCE     = mean confidence of successful (non-overridden) cases.
      5. Clamp all values to [0.05 .. 0.95] for safety.
    """
    db = SessionLocal()
    try:
        total = db.query(func.count(OrchestratorHistory.id)).scalar() or 0
        if total < MIN_SAMPLES:
            return {
                "approve_threshold": DEFAULT_APPROVE_THRESHOLD,
                "reject_threshold": DEFAULT_REJECT_THRESHOLD,
                "min_confidence": DEFAULT_MIN_CONFIDENCE,
                "source": "defaults",
                "samples": total,
            }

        # ── Mean risk per decision ──────────────────────────
        decision_stats = (
            db.query(
                OrchestratorHistory.decision,
                func.avg(OrchestratorHistory.overall_risk).label("mean_risk"),
                func.count(OrchestratorHistory.id).label("cnt"),
            )
            .group_by(OrchestratorHistory.decision)
            .all()
        )

        means = {row.decision: float(row.mean_risk) for row in decision_stats if row.mean_risk is not None}

        approve_mean = means.get("APPROVE", DEFAULT_APPROVE_THRESHOLD * 0.8)
        reject_mean = means.get("REJECT", DEFAULT_REJECT_THRESHOLD * 1.1)
        review_mean = means.get("REVIEW", (approve_mean + reject_mean) / 2)

        # Adaptive boundaries: midpoint between neighbouring categories
        adaptive_approve = _clamp((approve_mean + review_mean) / 2, 0.05, 0.45)
        adaptive_reject = _clamp((review_mean + reject_mean) / 2, 0.55, 0.95)

        # ── Mean confidence of non-overridden cases ─────────
        conf_result = (
            db.query(func.avg(OrchestratorHistory.confidence))
            .filter(OrchestratorHistory.human_override_decision.is_(None))
            .scalar()
        )
        adaptive_confidence = _clamp(
            float(conf_result) * 0.85 if conf_result else DEFAULT_MIN_CONFIDENCE,
            0.30,
            0.80,
        )

        return {
            "approve_threshold": round(adaptive_approve, 3),
            "reject_threshold": round(adaptive_reject, 3),
            "min_confidence": round(adaptive_confidence, 3),
            "source": "adaptive",
            "samples": total,
        }
    finally:
        db.close()


def get_agent_calibration(agent_step: str) -> Dict[str, float]:
    """
    Return per-agent calibration stats for prompt injection.
    Agents can use this to understand the historical distribution of their
    own risk scores — helps them self-calibrate outputs.
    """
    from model.rag_history import AgentHistory  # avoid circular at module level

    db = SessionLocal()
    try:
        stats = (
            db.query(
                func.avg(AgentHistory.risk).label("mean_risk"),
                func.avg(AgentHistory.confidence).label("mean_confidence"),
                func.count(AgentHistory.id).label("cnt"),
                func.min(AgentHistory.risk).label("min_risk"),
                func.max(AgentHistory.risk).label("max_risk"),
            )
            .filter(AgentHistory.agent_step == agent_step)
            .first()
        )

        if not stats or not stats.cnt or stats.cnt < 5:
            return {
                "mean_risk": 0.5,
                "mean_confidence": 0.7,
                "min_risk": 0.0,
                "max_risk": 1.0,
                "samples": 0,
                "source": "defaults",
            }

        return {
            "mean_risk": round(float(stats.mean_risk), 3),
            "mean_confidence": round(float(stats.mean_confidence), 3),
            "min_risk": round(float(stats.min_risk), 3),
            "max_risk": round(float(stats.max_risk), 3),
            "samples": int(stats.cnt),
            "source": "adaptive",
        }
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
