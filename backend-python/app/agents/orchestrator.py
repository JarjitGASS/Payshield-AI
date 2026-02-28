"""
Meta-Agent Orchestrator — fully autonomous with:
  1. Corrective error feedback between retries
  2. RAG context from historical orchestrator decisions
  3. Similar-flags RAG: fetch past cases with overlapping flags
  4. Full inter-agent communication via SessionState
  5. Adaptive threshold awareness for decision calibration
"""
import json
import asyncio
from dtos.agent_result import AgentResult
from dtos.meta_agent_result import MetaAgentResult
from dtos.session_state import SessionState, SessionStatus
from qwen.qwen import qwen_chat
from services.rag_service import (
    fetch_orchestrator_history,
    fetch_similar_flags_history,
    store_orchestrator_result,
)
from services.adaptive_threshold import get_adaptive_thresholds

AGENT_GOAL = (
    "Consolidate identity, behavioral, and network agent outputs "
    "and autonomously produce a final, evidence-based risk decision. "
    "Human intervention is only triggered if decision is REVIEW."
)

AGENT_STEP = "meta_agent_orchestrator"
MAX_RETRIES = 3


def _build_system_prompt(thresholds: dict) -> str:
    """Build system prompt with adaptive thresholds injected."""
    at = thresholds.get("approve_threshold", 0.3)
    rt = thresholds.get("reject_threshold", 0.7)
    mc = thresholds.get("min_confidence", 0.5)
    src = thresholds.get("source", "defaults")

    return f"""
You are a Meta-Agent Risk Orchestrator for a payment fraud detection system.
YOUR GOAL: {AGENT_GOAL}

RULES:
- Only reason from the 3 agent outputs provided.
- Resolve conflicting signals intelligently using the provided weights.
- Do not invent data. Return valid JSON only.
- You have full decision-making autonomy. Produce a final decision.

DECISION GUIDE (thresholds — source: {src}):
- overall_risk < {at}  AND confidence >= {mc} → APPROVE
- overall_risk {at}-{rt} OR confidence < {mc}  → REVIEW
- overall_risk > {rt}  AND confidence >= {mc} → REJECT

AGENT WEIGHTS (use these to compute overall_risk):
- Identity risk:   45%
- Behavioral risk: 25%
- Network risk:    30%

NOTE: If any agent has AGENT_FAILURE flag, escalate to REVIEW regardless of other scores.

OUTPUT FORMAT (strict JSON, no extra text):
{{{{
  "identity_risk": <float 0.0-1.0>,
  "behavior_risk": <float 0.0-1.0>,
  "network_risk": <float 0.0-1.0>,
  "overall_risk": <float 0.0-1.0>,
  "decision": "APPROVE" | "REVIEW" | "REJECT",
  "confidence": <float 0.0-1.0>,
  "explanation": "<2-3 sentence consolidated reasoning referencing all agent outputs>",
  "flags": [<all triggered flags combined from all agents>]
}}}}
"""


def _build_rag_context(all_flags: list) -> str:
    """Fetch historical orchestrator decisions and similar-flag cases (RAG)."""
    parts = []

    # Recent orchestrator decisions — returns a formatted string directly
    orch_history = fetch_orchestrator_history(limit=5)
    if orch_history:
        parts.append("\n--- HISTORICAL ORCHESTRATOR DECISIONS (RAG) ---")
        parts.append(orch_history)
        parts.append("Use these as calibration anchors for decision consistency.\n")

    # Cases with similar flags — also returns a formatted string
    if all_flags:
        similar = fetch_similar_flags_history(flags=all_flags, limit=3)
        if similar:
            parts.append("\n--- SIMILAR FLAG CASES (RAG) ---")
            parts.append(similar)
            parts.append(
                "These past cases had overlapping flags — ensure decision consistency.\n"
            )

    return "\n".join(parts)


def _build_inter_agent_context(state: SessionState) -> str:
    """
    INTER-AGENT COMMUNICATION:
    Provide the orchestrator with the full inter-agent communication
    picture — every agent's result, all accumulated flags, errors, and
    cross-agent correlation signals.
    """
    parts = []

    risks = {}
    if state.identity_result:
        risks["identity"] = state.identity_result.get("risk", 0.5)
    if state.behavioral_result:
        risks["behavioral"] = state.behavioral_result.get("risk", 0.5)
    if state.network_result:
        risks["network"] = state.network_result.get("risk", 0.5)

    if len(risks) >= 2:
        high_risk_agents = [k for k, v in risks.items() if v > 0.6]
        if len(high_risk_agents) >= 2:
            parts.append(
                f"\n--- CROSS-AGENT CORRELATION ---\n"
                f"  ⚠ Multiple agents report elevated risk: {high_risk_agents}\n"
                f"  This cross-agent agreement significantly increases confidence "
                f"in a REJECT decision.\n"
            )

        low_risk_agents = [k for k, v in risks.items() if v < 0.3]
        high_risk = [k for k, v in risks.items() if v > 0.6]
        if low_risk_agents and high_risk:
            parts.append(
                f"\n--- CROSS-AGENT CONFLICT ---\n"
                f"  ⚠ Conflicting signals: {low_risk_agents} report low risk while "
                f"{high_risk} report high risk.\n"
                f"  Resolve carefully — conflicting signals typically warrant REVIEW.\n"
            )

    if state.errors:
        parts.append(f"\n--- SESSION ERRORS ---\n  {state.errors}")

    if state.retry_count > 0:
        parts.append(
            f"\n--- SESSION RETRIES ---\n"
            f"  Total retries across all agents: {state.retry_count}\n"
            f"  High retry count may indicate ambiguous input data.\n"
        )

    return "\n".join(parts)


def _build_user_prompt(
    identity: AgentResult,
    behavioral: AgentResult,
    network: AgentResult,
    state: SessionState,
) -> str:
    all_flags = identity.flags + behavioral.flags + network.flags
    rag_ctx = _build_rag_context(all_flags)
    inter_agent_ctx = _build_inter_agent_context(state)

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
{rag_ctx}{inter_agent_ctx}

Return the consolidated JSON decision only.
"""


def _build_corrective_prompt(
    identity: AgentResult,
    behavioral: AgentResult,
    network: AgentResult,
    state: SessionState,
    last_error: str,
    attempt: int,
) -> str:
    """Build a retry prompt injecting the specific error from the previous attempt."""
    base = _build_user_prompt(identity, behavioral, network, state)
    return f"""{base}

--- CORRECTIVE FEEDBACK (attempt {attempt}) ---
Your previous output was INVALID. The error was:
  \"{last_error}\"

FIX INSTRUCTIONS:
- Ensure your response is ONLY valid JSON (no markdown, no extra text).
- All risk/confidence fields must be floats between 0.0 and 1.0.
- decision must be exactly "APPROVE", "REVIEW", or "REJECT".
- flags must be a JSON array of strings.
Return corrected JSON only.
"""


async def run_orchestrator(
    identity: AgentResult,
    behavioral: AgentResult,
    network: AgentResult,
    state: SessionState,
) -> MetaAgentResult:
    """
    DECISION MAKING AUTONOMY + REASON-ACT LOOP (async):
    1. REASON: Consolidate all 3 agent outputs + RAG + inter-agent context.
    2. ACT:    Call Qwen (offloaded to thread) to produce autonomous final decision.
    3. VALIDATE: Parse and validate the meta-agent output.
    4. CORRECT: If output invalid, inject corrective feedback and retry.
    5. STORE:  Persist result to RAG history for future sessions.
    6. FALLBACK: If all retries fail, escalate entire session to REVIEW.
    """
    state.transition(SessionStatus.ORCHESTRATING, step=f"Running {AGENT_STEP}")

    # Fetch adaptive thresholds (sync, offloaded)
    thresholds = await asyncio.to_thread(get_adaptive_thresholds)
    system_prompt = _build_system_prompt(thresholds)

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

        await asyncio.to_thread(
            store_orchestrator_result,
            state.session_id,
            fallback.identity_risk,
            fallback.behavior_risk,
            fallback.network_risk,
            fallback.overall_risk,
            fallback.decision,
            fallback.confidence,
            fallback.explanation,
            fallback.flags,
        )
        return fallback

    # Build RAG context (sync DB, offloaded)
    user_prompt = await asyncio.to_thread(_build_user_prompt, identity, behavioral, network, state)
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            prompt = (
                _build_corrective_prompt(
                    identity, behavioral, network, state, last_error, attempt
                )
                if last_error else user_prompt
            )

            # Offload blocking Qwen HTTP call to a thread
            raw = await asyncio.to_thread(qwen_chat, system_prompt, prompt)
            data = json.loads(raw)

            result = MetaAgentResult(**data)

            scores = [
                result.identity_risk, result.behavior_risk,
                result.network_risk, result.overall_risk, result.confidence
            ]
            if not all(0.0 <= s <= 1.0 for s in scores):
                raise ValueError(f"Score out of range in meta-agent output: {scores}")
            if result.decision not in ["APPROVE", "REVIEW", "REJECT"]:
                raise ValueError(f"Invalid decision: {result.decision}")

            # Store result (sync DB write, offloaded)
            await asyncio.to_thread(
                store_orchestrator_result,
                state.session_id,
                result.identity_risk,
                result.behavior_risk,
                result.network_risk,
                result.overall_risk,
                result.decision,
                result.confidence,
                result.explanation,
                result.flags,
            )

            state.meta_result = result.model_dump()
            state.final_decision = result.decision
            state.final_overall_risk = result.overall_risk
            state.merge_flags(result.flags)
            return result

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            last_error = str(e)
            state.retry_count += 1
            error_msg = f"{AGENT_STEP} attempt {attempt} failed: {e}"
            state.errors.append(error_msg)
            print(f"[ReasonActLoop] {error_msg}. Injecting corrective feedback...")

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

    await asyncio.to_thread(
        store_orchestrator_result,
        state.session_id,
        fallback.identity_risk,
        fallback.behavior_risk,
        fallback.network_risk,
        fallback.overall_risk,
        fallback.decision,
        fallback.confidence,
        fallback.explanation,
        fallback.flags,
    )
    return fallback
