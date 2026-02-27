"""
Guardrails — Deterministic policy enforcement with adaptive thresholds.

Replaces hardcoded thresholds with data-driven adaptive thresholds
computed from historical orchestrator decisions. Falls back to safe
defaults when insufficient history exists.
"""
from dtos.meta_agent_result import MetaAgentResult
from dtos.session_state import SessionState, SessionStatus
from services.adaptive_threshold import get_adaptive_thresholds
from services.rag_service import store_orchestrator_result

# Fallback defaults (used if adaptive service is unreachable)
FALLBACK_APPROVE = 0.3
FALLBACK_REJECT = 0.7
FALLBACK_CONFIDENCE = 0.5


def _get_thresholds() -> dict:
    """
    Fetch adaptive thresholds, falling back to hardcoded defaults
    if the service raises an exception.
    """
    try:
        return get_adaptive_thresholds()
    except Exception as e:
        print(f"[Guardrails] Adaptive threshold service failed: {e}. Using fallback defaults.")
        return {
            "approve_threshold": FALLBACK_APPROVE,
            "reject_threshold": FALLBACK_REJECT,
            "min_confidence": FALLBACK_CONFIDENCE,
            "source": "fallback",
            "samples": 0,
        }


def validate(result: MetaAgentResult, thresholds: dict = None) -> bool:
    """
    Validate the meta-agent result against adaptive thresholds.
    Returns True if the output is structurally valid and internally consistent.
    """
    if thresholds is None:
        thresholds = _get_thresholds()

    approve_t = thresholds["approve_threshold"]
    reject_t = thresholds["reject_threshold"]

    try:
        scores = [
            result.identity_risk, result.behavior_risk,
            result.network_risk, result.overall_risk, result.confidence
        ]
        # All scores must be within valid range
        if not all(0.0 <= s <= 1.0 for s in scores):
            return False
        # Decision must be a valid option
        if result.decision not in ["APPROVE", "REVIEW", "REJECT"]:
            return False
        # Decision must be consistent with risk score (using adaptive thresholds)
        if result.overall_risk > reject_t and result.decision == "APPROVE":
            return False
        if result.overall_risk < approve_t and result.decision == "REJECT":
            return False
        # Explanation must not be empty
        if not result.explanation or len(result.explanation.strip()) == 0:
            return False
        return True
    except Exception:
        return False


def enforce_policy(result: MetaAgentResult, state: SessionState) -> MetaAgentResult:
    """
    DETERMINISTIC POLICY ENFORCEMENT with adaptive thresholds:

    This is the final guardrail layer. It overrides the AI decision
    if the output is invalid or inconsistent with data-driven thresholds.

    Priority order:
    1. AGENT_FAILURE or ORCHESTRATOR_FAILURE → always REVIEW
    2. Output validation fails → REVIEW
    3. Low confidence (adaptive) → REVIEW
    4. High risk (adaptive) → REJECT
    5. Low risk (adaptive) → APPROVE
    6. Mid range → REVIEW

    After enforcement, the final result is stored to RAG history
    for future adaptive threshold computation.
    """
    state.transition(SessionStatus.GUARDRAIL_CHECK, step="Enforcing policy guardrails")

    # ── Fetch adaptive thresholds ───────────────────────────
    thresholds = _get_thresholds()
    approve_t = thresholds["approve_threshold"]
    reject_t = thresholds["reject_threshold"]
    min_conf = thresholds["min_confidence"]

    print(
        f"[Guardrails] Using {thresholds['source']} thresholds "
        f"(samples={thresholds['samples']}): "
        f"approve<{approve_t}, reject>{reject_t}, min_conf={min_conf}"
    )

    # Rule 1: Any system failure flag → force REVIEW
    critical_flags = {"AGENT_FAILURE", "ORCHESTRATOR_FAILURE"}
    if any(f in critical_flags for f in result.flags):
        result.decision = "REVIEW"
        result.explanation += " [GUARDRAIL: System failure flag detected, escalated to REVIEW]"
        state.final_decision = "REVIEW"
        state.transition(SessionStatus.REVIEW, step="Escalated: system failure flag")
        _store_final_result(result, state)
        return result

    # Rule 2: Invalid AI output → force REVIEW
    if not validate(result, thresholds):
        result.decision = "REVIEW"
        result.explanation += " [GUARDRAIL: Output failed validation, escalated to REVIEW]"
        state.final_decision = "REVIEW"
        state.transition(SessionStatus.REVIEW, step="Escalated: validation failed")
        _store_final_result(result, state)
        return result

    # Rule 3-6: Deterministic policy enforcement with ADAPTIVE thresholds
    risk = result.overall_risk
    conf = result.confidence

    if conf < min_conf:
        result.decision = "REVIEW"
        result.explanation += f" [GUARDRAIL: Low confidence ({conf:.2f} < {min_conf:.2f})]"
        state.transition(SessionStatus.REVIEW, step="Escalated: low confidence")
    elif risk > reject_t:
        result.decision = "REJECT"
        result.explanation += f" [GUARDRAIL: High risk ({risk:.2f} > {reject_t:.2f})]"
        state.transition(SessionStatus.COMPLETE, step="Decision: REJECT")
    elif risk < approve_t:
        result.decision = "APPROVE"
        result.explanation += f" [GUARDRAIL: Low risk ({risk:.2f} < {approve_t:.2f})]"
        state.transition(SessionStatus.COMPLETE, step="Decision: APPROVE")
    else:
        result.decision = "REVIEW"
        result.explanation += (
            f" [GUARDRAIL: Mid-range risk ({risk:.2f} in [{approve_t:.2f}–{reject_t:.2f}])]"
        )
        state.transition(SessionStatus.REVIEW, step="Decision: REVIEW (mid-range risk)")

    state.final_decision = result.decision
    state.final_overall_risk = result.overall_risk

    # ── Store final decision to RAG for future threshold adaptation ──
    _store_final_result(result, state)

    return result


def _store_final_result(result: MetaAgentResult, state: SessionState) -> None:
    """Persist the guardrail-enforced result to RAG history."""
    try:
        store_orchestrator_result(
            session_id=state.session_id,
            identity_risk=result.identity_risk,
            behavior_risk=result.behavior_risk,
            network_risk=result.network_risk,
            overall_risk=result.overall_risk,
            decision=result.decision,
            confidence=result.confidence,
            explanation=result.explanation,
            flags=result.flags,
        )
    except Exception as e:
        print(f"[Guardrails] Failed to store result to RAG: {e}")
