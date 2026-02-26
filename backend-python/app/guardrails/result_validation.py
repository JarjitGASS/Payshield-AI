from model.meta_agent_result import MetaAgentResult

APPROVE_THRESHOLD = 0.3
REJECT_THRESHOLD = 0.7
MIN_CONFIDENCE = 0.5

def validate(result: MetaAgentResult) -> bool:
    """Validate all score ranges and decision consistency."""
    scores = [
        result.identity_risk, result.behavior_risk,
        result.network_risk, result.overall_risk, result.confidence
    ]
    # All scores must be 0-1
    if not all(0.0 <= s <= 1.0 for s in scores):
        return False
    # Decision must be valid
    if result.decision not in ["APPROVE", "REVIEW", "REJECT"]:
        return False
    # Decision must be consistent with risk
    if result.overall_risk > 0.7 and result.decision == "APPROVE":
        return False
    if result.overall_risk < 0.3 and result.decision == "REJECT":
        return False
    return True

def enforce_policy(result: MetaAgentResult) -> MetaAgentResult:
    """Deterministic policy enforcement — overrides AI decision if needed."""

    # Step 1: Validate AI output
    if not validate(result):
        result.decision = "REVIEW"
        result.explanation += " [GUARDRAIL: Output failed validation, escalated to REVIEW]"
        return result

    # Step 2: Enforce policy rules
    risk = result.overall_risk
    conf = result.confidence

    if conf < MIN_CONFIDENCE:
        result.decision = "REVIEW"
    elif risk < APPROVE_THRESHOLD:
        result.decision = "APPROVE"
    elif risk > REJECT_THRESHOLD:
        result.decision = "REJECT"
    else:
        result.decision = "REVIEW"

    return result