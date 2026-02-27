"""
Synthetic Network Agent — fully autonomous with:
  1. Corrective error feedback between retries
  2. RAG context from historical network assessments
  3. Upstream context from SessionState (identity + behavioral results)
  4. Self-calibration from adaptive thresholds
  5. Inter-agent communication: correlates with upstream agent flags
"""
import json
from dtos.agent_result import AgentResult
from dtos.network_input import NetworkInput
from dtos.session_state import SessionState, SessionStatus
from qwen.qwen import qwen_chat
from services.rag_service import fetch_agent_history, store_agent_result
from services.tool_dispatch import get_tools_for_agent
from services.adaptive_threshold import get_agent_calibration

AGENT_GOAL = (
    "Detect synthetic identity clusters and mule account networks "
    "using shared device, shared IP, account age, and cross-merchant reuse signals."
)

AGENT_STEP = "synthetic_network_agent"
MAX_RETRIES = 3

SYSTEM_PROMPT = f"""
You are a Synthetic Network Agent for a payment fraud detection system.
YOUR GOAL: {AGENT_GOAL}

RULES:
- Only use the signals provided. Do not invent or assume missing data.
- If a signal is missing or unknown, treat it as neutral (0.5).
- Return valid JSON only.

OUTPUT FORMAT (strict JSON, no extra text):
{{{{
  "risk": <float 0.0-1.0>,
  "confidence": <float 0.0-1.0>,
  "flags": [<list of triggered risk flags>],
  "explanation": "<1-2 sentence reasoning referencing only provided signals>",
  "agent_step": "synthetic_network_agent"
}}}}

AVAILABLE FLAGS:
- DEVICE_SHARED_NETWORK, IP_CLUSTER, CROSS_MERCHANT_REUSE,
  RAPID_ACCOUNT_CREATION
"""


def _build_rag_context() -> str:
    """Fetch historical network assessments to augment the prompt (RAG)."""
    history = fetch_agent_history(agent_step=AGENT_STEP, limit=5, min_confidence=0.6)
    if not history:
        return ""
    return history


def _build_calibration_context() -> str:
    """Fetch self-calibration stats from adaptive thresholds."""
    cal = get_agent_calibration(AGENT_STEP)
    if cal["source"] == "defaults":
        return ""
    return (
        f"\n--- SELF-CALIBRATION (from {cal['samples']} past assessments) ---\n"
        f"  Your historical mean risk: {cal['mean_risk']}, range [{cal['min_risk']}–{cal['max_risk']}]\n"
        f"  Your historical mean confidence: {cal['mean_confidence']}\n"
        f"  Calibrate your output to stay consistent with your own past assessments.\n"
    )


def _build_upstream_context(state: SessionState) -> str:
    """
    INTER-AGENT COMMUNICATION:
    Inject upstream identity AND behavioral agent results so this agent
    can detect correlations across all three risk dimensions.
    """
    parts = []

    if state.identity_result:
        ir = state.identity_result
        parts.append(
            f"\n--- UPSTREAM: Identity Agent Results ---\n"
            f"  Identity risk: {ir.get('risk', 'N/A')}, "
            f"confidence: {ir.get('confidence', 'N/A')}\n"
            f"  Identity flags: {ir.get('flags', [])}\n"
        )

    if state.behavioral_result:
        br = state.behavioral_result
        parts.append(
            f"\n--- UPSTREAM: Behavioral Agent Results ---\n"
            f"  Behavioral risk: {br.get('risk', 'N/A')}, "
            f"confidence: {br.get('confidence', 'N/A')}\n"
            f"  Behavioral flags: {br.get('flags', [])}\n"
        )

    if state.identity_result and state.behavioral_result:
        id_risk = state.identity_result.get('risk', 0.5)
        bh_risk = state.behavioral_result.get('risk', 0.5)
        if id_risk > 0.6 and bh_risk > 0.6:
            parts.append(
                f"  ⚠ CORRELATION ALERT: Both identity ({id_risk:.2f}) and behavioral "
                f"({bh_risk:.2f}) show elevated risk. Network anomalies in this context "
                f"should be weighted more heavily.\n"
            )

    if state.flags:
        parts.append(f"\n--- ACCUMULATED SESSION FLAGS ---\n  {state.flags}")

    if state.errors:
        parts.append(f"\n--- UPSTREAM ERRORS ---\n  {state.errors}")

    return "\n".join(parts)


def _build_tools_context() -> str:
    """List available tools for the agent's awareness."""
    tools = get_tools_for_agent(AGENT_STEP)
    if not tools:
        return ""
    lines = ["\n--- AVAILABLE TOOLS ---"]
    for name, desc in tools.items():
        lines.append(f"  - {name}: {desc}")
    return "\n".join(lines)


def _build_user_prompt(features: NetworkInput, state: SessionState, rag_ctx: str) -> str:
    cal_ctx = _build_calibration_context()
    upstream_ctx = _build_upstream_context(state)
    tools_ctx = _build_tools_context()

    return f"""
Evaluate synthetic network risk from these signals:

- shared_device_count: {features.shared_device_count}
  (>1 = same device fingerprint on multiple accounts)
- shared_ip_count: {features.shared_ip_count}
  (>3 in 30 days = suspicious IP cluster)
- cross_merchant_reuse: {features.cross_merchant_reuse}
  (true = device/phone seen across different merchants)
{rag_ctx}{cal_ctx}{upstream_ctx}{tools_ctx}

Return JSON only.
"""


def _build_corrective_prompt(
    features: NetworkInput, state: SessionState,
    rag_ctx: str, last_error: str, attempt: int
) -> str:
    """Build a retry prompt injecting the specific error from the previous attempt."""
    base = _build_user_prompt(features, state, rag_ctx)
    return f"""{base}

--- CORRECTIVE FEEDBACK (attempt {attempt}) ---
Your previous output was INVALID. The error was:
  \"{last_error}\"

FIX INSTRUCTIONS:
- Ensure your response is ONLY valid JSON (no markdown, no extra text).
- risk and confidence must be floats between 0.0 and 1.0.
- flags must be a JSON array of strings.
- agent_step must be "{AGENT_STEP}".
Return corrected JSON only.
"""


def _run_tool_enrichment(features: NetworkInput) -> None:
    """
    Fix 1 — ACTION CAPABILITY: invoke tools before LLM to enrich features in-place.
    Currently a no-op placeholder — network features come from upstream DB queries.
    """
    pass


def run_network_agent(features: NetworkInput, state: SessionState) -> AgentResult:
    """
    Full Reason-Act Loop:
      Fix 1 — Tool dispatch BEFORE LLM call
      Fix 2 — RAG fetch BEFORE LLM, store AFTER success
      Fix 4 — Upstream SessionState context injected into prompt
      Corrective feedback on retry
    """
    state.transition(SessionStatus.AGENT_RUNNING, step=f"Running {AGENT_STEP}")

    # Fix 1: Tool dispatch — enrich features before building the prompt
    _run_tool_enrichment(features)

    # Fix 2: RAG fetch — retrieve history before first LLM call
    rag_ctx = _build_rag_context()

    # Build initial prompt (includes Fix 4: upstream context from state)
    user_prompt = _build_user_prompt(features, state, rag_ctx)
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            prompt = (
                _build_corrective_prompt(features, state, rag_ctx, last_error, attempt)
                if last_error else user_prompt
            )

            raw = qwen_chat(SYSTEM_PROMPT, prompt)
            data = json.loads(raw)

            result = AgentResult(**data)

            if not (0.0 <= result.risk <= 1.0 and 0.0 <= result.confidence <= 1.0):
                raise ValueError(f"Score out of range: risk={result.risk}, confidence={result.confidence}")

            # Fix 2: Store result to RAG history after successful parse
            store_agent_result(
                session_id=state.session_id,
                agent_step=AGENT_STEP,
                input_features=features.model_dump(),
                risk=result.risk,
                confidence=result.confidence,
                flags=result.flags,
                explanation=result.explanation,
            )

            # Fix 4: Write to SessionState for downstream agents to read
            state.network_result = result.model_dump()
            state.merge_flags(result.flags)
            return result

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            last_error = str(e)
            state.retry_count += 1
            error_msg = f"{AGENT_STEP} attempt {attempt} failed: {e}"
            state.errors.append(error_msg)
            print(f"[ReasonActLoop] {error_msg}. Injecting corrective feedback...")

    fallback = AgentResult(
        risk=0.5,
        confidence=0.0,
        flags=["AGENT_FAILURE"],
        explanation=f"{AGENT_STEP} failed after {MAX_RETRIES} retries. Last error: {last_error}",
        agent_step=AGENT_STEP,
    )
    state.network_result = fallback.model_dump()
    state.merge_flags(fallback.flags)
    return fallback
