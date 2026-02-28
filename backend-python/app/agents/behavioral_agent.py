"""
Behavioral Anomaly Agent — fully autonomous with:
  1. Corrective error feedback between retries
  2. RAG context from historical behavioral assessments
  3. Tool dispatch for navigation/click entropy
  4. Upstream context from SessionState (identity results)
  5. Self-calibration from adaptive thresholds
"""
import json
import asyncio
from dtos.agent_result import AgentResult
from dtos.behavioral_input import BehavioralInput
from dtos.session_state import SessionState, SessionStatus
from qwen.qwen import qwen_chat
from services.rag_service import fetch_agent_history, store_agent_result
from services.tool_dispatch import dispatch_tool, get_tools_for_agent
from services.adaptive_threshold import get_agent_calibration

AGENT_GOAL = (
    "Detect bots, scripts, or suspicious human behavior "
    "using typing cadence, mouse entropy, session duration, login hour, "
    "and navigation consistency signals."
)

AGENT_STEP = "behavioral_agent"
MAX_RETRIES = 3

SYSTEM_PROMPT = f"""
You are a Behavioral Anomaly Agent for a payment fraud detection system.
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
  "agent_step": "behavioral_agent"
}}}}

AVAILABLE FLAGS:
- BOT_TYPING_PATTERN, ABNORMAL_MOUSE, TOO_FAST_SESSION,
  ODD_LOGIN_HOUR, UNUSUAL_NAVIGATION
"""


def _build_rag_context() -> str:
    """Fetch historical behavioral assessments to augment the prompt (RAG)."""
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
    Inject upstream identity agent results so this agent can correlate
    behavioral anomalies with identity risk signals.
    """
    parts = []

    if state.identity_result:
        ir = state.identity_result
        parts.append(
            f"\n--- UPSTREAM: Identity Agent Results ---\n"
            f"  Identity risk: {ir.get('risk', 'N/A')}, "
            f"confidence: {ir.get('confidence', 'N/A')}\n"
            f"  Identity flags: {ir.get('flags', [])}\n"
            f"  Context: If identity is already flagged, behavioral anomalies "
            f"carry more weight. Correlate signals across agents.\n"
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


def _build_user_prompt(features: BehavioralInput, state: SessionState, rag_ctx: str) -> str:
    cal_ctx = _build_calibration_context()
    upstream_ctx = _build_upstream_context(state)
    tools_ctx = _build_tools_context()

    return f"""
Evaluate behavioral anomaly risk from these signals:

- typing_cadence_variance: {features.typing_cadence_variance}ms
  (very low = bot uniform typing, very high = scripted paste)
- mouse_entropy_score: {features.mouse_entropy_score}
  (0.0 = robotic linear movement, 1.0 = natural human movement)
- session_duration_sec: {features.session_duration_sec}s
  (very fast = bot, very slow = distracted/scripted)
- login_hour: {features.login_hour}
  (unusual hours like 2-4am = suspicious)
- navigation_consistency_score: {features.navigation_consistency_score}
  (1.0 = normal flow, 0.0 = erratic/skipped steps)
{rag_ctx}{cal_ctx}{upstream_ctx}{tools_ctx}

Return JSON only.
"""


def _build_corrective_prompt(
    features: BehavioralInput, state: SessionState,
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


def _run_tool_enrichment(features: BehavioralInput, state: SessionState) -> None:
    """
    Fix 1 — ACTION CAPABILITY: invoke tools before LLM to enrich features in-place.
    Recompute navigation consistency from live session data if available.
    """
    if state.session_id:
        result = dispatch_tool("navigation_consistency_score", user_id=state.session_id)
        if isinstance(result, (int, float)):
            features.navigation_consistency_score = float(result)
        elif isinstance(result, dict) and "error" not in result:
            score = result.get("score") or result.get("navigation_consistency_score")
            if score is not None:
                features.navigation_consistency_score = float(score)


async def run_behavioral_agent(features: BehavioralInput, state: SessionState) -> AgentResult:
    """
    Full Reason-Act Loop (async):
      Fix 1 — Tool dispatch BEFORE LLM call (enriches navigation consistency)
      Fix 2 — RAG fetch BEFORE LLM, store AFTER success
      Fix 4 — Upstream SessionState context injected into prompt
      Corrective feedback on retry
      qwen_chat is blocking — offloaded to a thread via asyncio.to_thread()
    """
    state.transition(SessionStatus.AGENT_RUNNING, step=f"Running {AGENT_STEP}")

    # Fix 1: Tool dispatch — sync, fast
    _run_tool_enrichment(features, state)

    # Fix 2: RAG fetch — sync DB read, offloaded to thread
    rag_ctx = await asyncio.to_thread(_build_rag_context)

    # Build initial prompt (includes Fix 4: upstream context from state)
    user_prompt = _build_user_prompt(features, state, rag_ctx)
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            prompt = (
                _build_corrective_prompt(features, state, rag_ctx, last_error, attempt)
                if last_error else user_prompt
            )

            # Offload blocking Qwen HTTP call to a thread
            raw = await asyncio.to_thread(qwen_chat, SYSTEM_PROMPT, prompt)
            data = json.loads(raw)

            result = AgentResult(**data)

            if not (0.0 <= result.risk <= 1.0 and 0.0 <= result.confidence <= 1.0):
                raise ValueError(f"Score out of range: risk={result.risk}, confidence={result.confidence}")

            # Fix 2: Store result (sync DB write, offloaded)
            await asyncio.to_thread(
                store_agent_result,
                state.session_id,
                AGENT_STEP,
                features.model_dump(),
                result.risk,
                result.confidence,
                result.flags,
                result.explanation,
            )

            # Fix 4: Write to SessionState for downstream agents to read
            state.behavioral_result = result.model_dump()
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
    state.behavioral_result = fallback.model_dump()
    state.merge_flags(fallback.flags)
    return fallback
