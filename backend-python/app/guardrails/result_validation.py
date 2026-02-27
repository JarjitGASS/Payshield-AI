from model.meta_agent_result import MetaAgentResult
from model.session_state import SessionState, SessionStatus

APPROVE_THRESHOLD = 0.3
REJECT_THRESHOLD = 0.7
MIN_CONFIDENCE = 0.5


def validate(result: MetaAgentResult) -> bool:
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
        # Decision must be consistent with risk score
        if result.overall_risk > REJECT_THRESHOLD and result.decision == "APPROVE":
            return False
        if result.overall_risk < APPROVE_THRESHOLD and result.decision == "REJECT":
            return False
        # Explanation must not be empty
        if not result.explanation or len(result.explanation.strip()) == 0:
            return False
        return True
    except Exception:
        return False


def enforce_policy(result: MetaAgentResult, state: SessionState) -> MetaAgentResult:
    """
    DETERMINISTIC POLICY ENFORCEMENT:
    This is the final guardrail layer. It overrides the AI decision
    if the output is invalid or inconsistent with business thresholds.

    Priority order:
    1. AGENT_FAILURE or ORCHESTRATOR_FAILURE → always REVIEW
    2. Output validation fails → REVIEW
    3. Low confidence → REVIEW
    4. High risk → REJECT
    5. Low risk → APPROVE
    6. Mid range → REVIEW
    """
    state.transition(SessionStatus.GUARDRAIL_CHECK, step="Enforcing policy guardrails")

    # Rule 1: Any system failure flag → force REVIEW
    critical_flags = {"AGENT_FAILURE", "ORCHESTRATOR_FAILURE"}
    if any(f in critical_flags for f in result.flags):
        result.decision = "REVIEW"
        result.explanation += " [GUARDRAIL: System failure flag detected, escalated to REVIEW]"
        state.final_decision = "REVIEW"
        state.transition(SessionStatus.REVIEW, step="Escalated: system failure flag")
        return result

    # Rule 2: Invalid AI output → force REVIEW
    if not validate(result):
        result.decision = "REVIEW"
        result.explanation += " [GUARDRAIL: Output failed validation, escalated to REVIEW]"
        state.final_decision = "REVIEW"
        state.transition(SessionStatus.REVIEW, step="Escalated: validation failed")
        return result

    # Rule 3-6: Deterministic policy enforcement
    risk = result.overall_risk
    conf = result.confidence

    if conf < MIN_CONFIDENCE:
        result.decision = "REVIEW"
        state.transition(SessionStatus.REVIEW, step="Escalated: low confidence")
    elif risk > REJECT_THRESHOLD:
        result.decision = "REJECT"
        state.transition(SessionStatus.COMPLETE, step="Decision: REJECT")
    elif risk < APPROVE_THRESHOLD:
        result.decision = "APPROVE"
        state.transition(SessionStatus.COMPLETE, step="Decision: APPROVE")
    else:
        result.decision = "REVIEW"
        state.transition(SessionStatus.REVIEW, step="Decision: REVIEW (mid-range risk)")

    state.final_decision = result.decision
    state.final_overall_risk = result.overall_risk
    return result
