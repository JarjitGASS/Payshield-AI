import json
from model.agent_result import AgentResult
from model.meta_agent_result import MetaAgentResult
from model.session_state import SessionState, SessionStatus
from qwen.qwen import qwen_chat

# ─────────────────────────────────────────────────────────────
# GOAL: Consolidate all agent outputs and autonomously produce
#       a final risk decision (APPROVE / REVIEW / REJECT).
#       Human intervention is only triggered on REVIEW.
# ─────────────────────────────────────────────────────────────
AGENT_GOAL = (
    "Consolidate identity, behavioral, and network agent outputs "
    "and autonomously produce a final, evidence-based risk decision. "
    "Human intervention is only triggered if decision is REVIEW."
)

AGENT_STEP = "meta_agent_orchestrator"
MAX_RETRIES = 2

SYSTEM_PROMPT = f"""
You are a Meta-Agent Risk Orchestrator for a payment fraud detection system.
YOUR GOAL: {AGENT_GOAL}

RULES:
- Only reason from the 3 agent outputs provided.
- Resolve conflicting signals intelligently using the provided weights.
- Do not invent data. Return valid JSON only.
- You have full decision-making autonomy. Produce a final decision.

DECISION GUIDE (deterministic thresholds for your reference):
- overall_risk < 0.3  AND confidence >= 0.5 → APPROVE
- overall_risk 0.3-0.7 OR confidence < 0.5  → REVIEW
- overall_risk > 0.7  AND confidence >= 0.5 → REJECT

AGENT WEIGHTS (use these to compute overall_risk):
- Identity risk:   45%
- Behavioral risk: 25%
- Network risk:    30%

NOTE: If any agent has AGENT_FAILURE flag, escalate to REVIEW regardless of other scores.

OUTPUT FORMAT (strict JSON, no extra text):
{{
  "identity_risk": <float 0.0-1.0>,
  "behavior_risk": <float 0.0-1.0>,
  "network_risk": <float 0.0-1.0>,
  "overall_risk": <float 0.0-1.0>,
  "decision": "APPROVE" | "REVIEW" | "REJECT",
  "confidence": <float 0.0-1.0>,
  "explanation": "<2-3 sentence consolidated reasoning referencing all agent outputs>",
  "flags": [<all triggered flags combined from all agents>]
}}
"""


def _build_user_prompt(
    identity: AgentResult,
    behavioral: AgentResult,
    network: AgentResult,
) -> str:
    return f"""
Consolidate these 3 agent outputs into a final autonomous risk decision:

IDENTITY AGENT (weight: 45%):
- risk: {identity.risk}
- flags: {identity.flags}
- explanation: {identity.explanation}
- confidence: {identity.confidence}

BEHAVIORAL AGENT (weight: 25%):
- risk: {behavioral.risk}
- flags: {behavioral.flags}
- explanation: {behavioral.explanation}
- confidence: {behavioral.confidence}

NETWORK AGENT (weight: 30%):
- risk: {network.risk}
- flags: {network.flags}
- explanation: {network.explanation}
- confidence: {network.confidence}

Return the consolidated JSON decision only.
"""


def run_orchestrator(
    identity: AgentResult,
    behavioral: AgentResult,
    network: AgentResult,
    state: SessionState,
) -> MetaAgentResult:
    """
    DECISION MAKING AUTONOMY + REASON-ACT LOOP:
    1. REASON: Consolidate all 3 agent outputs into a single prompt.
    2. ACT:    Call Qwen to produce autonomous final decision.
    3. VALIDATE: Parse and validate the meta-agent output.
    4. RETRY:  If output is invalid, retry up to MAX_RETRIES times.
    5. FALLBACK: If all retries fail, escalate entire session to REVIEW.

    The orchestrator has full decision-making autonomy.
    Human intervention is only triggered if decision = REVIEW.
    """
    state.transition(SessionStatus.ORCHESTRATING, step=f"Running {AGENT_STEP}")

    # If any agent has AGENT_FAILURE, force REVIEW before even calling LLM
    all_flags = identity.flags + behavioral.flags + network.flags
    if "AGENT_FAILURE" in all_flags:
        fallback = MetaAgentResult(
            identity_risk=identity.risk,
            behavior_risk=behavioral.risk,
            network_risk=network.risk,
            overall_risk=0.5,
            decision="REVIEW",
            confidence=0.0,
            explanation="One or more agents failed. Session escalated to human review.",
            flags=list(set(all_flags)),
        )
        state.meta_result = fallback.model_dump()
        state.final_decision = "REVIEW"
        state.final_overall_risk = 0.5
        state.transition(SessionStatus.REVIEW, step="Escalated due to AGENT_FAILURE")
        return fallback

    user_prompt = _build_user_prompt(identity, behavioral, network)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = qwen_chat(SYSTEM_PROMPT, user_prompt)
            data = json.loads(raw)

            result = MetaAgentResult(**data)

            # Validate all score fields
            scores = [
                result.identity_risk, result.behavior_risk,
                result.network_risk, result.overall_risk, result.confidence
            ]
            if not all(0.0 <= s <= 1.0 for s in scores):
                raise ValueError(f"Score out of range in meta-agent output: {scores}")
            if result.decision not in ["APPROVE", "REVIEW", "REJECT"]:
                raise ValueError(f"Invalid decision: {result.decision}")

            # Store result in session state
            state.meta_result = result.model_dump()
            state.final_decision = result.decision
            state.final_overall_risk = result.overall_risk
            state.merge_flags(result.flags)
            return result

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            state.retry_count += 1
            error_msg = f"{AGENT_STEP} attempt {attempt} failed: {e}"
            state.errors.append(error_msg)
            print(f"[ReasonActLoop] {error_msg}. Retrying...")

    # All retries exhausted — safe fallback to REVIEW
    fallback = MetaAgentResult(
        identity_risk=identity.risk,
        behavior_risk=behavioral.risk,
        network_risk=network.risk,
        overall_risk=0.5,
        decision="REVIEW",
        confidence=0.0,
        explanation=f"{AGENT_STEP} failed after {MAX_RETRIES} retries. Session escalated to human review.",
        flags=list(set(all_flags + ["ORCHESTRATOR_FAILURE"])),
    )
    state.meta_result = fallback.model_dump()
    state.final_decision = "REVIEW"
    state.final_overall_risk = 0.5
    state.merge_flags(fallback.flags)
    state.transition(SessionStatus.REVIEW, step="Orchestrator failed, escalated to REVIEW")
    return fallback
