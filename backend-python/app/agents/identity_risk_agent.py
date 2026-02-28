"""
Identity Risk Agent — fully autonomous with:
  1. Corrective error feedback between retries
  2. RAG context from historical identity assessments
  3. Tool dispatch for on-demand service invocations
  4. Upstream context from SessionState
  5. Self-calibration from adaptive thresholds
"""
import json
import asyncio
from dtos.agent_result import AgentResult
from dtos.identity_input import IdentityInput
from dtos.session_state import SessionState, SessionStatus
from qwen.qwen import qwen_chat
from services.rag_service import fetch_agent_history, store_agent_result
from services.tool_dispatch import dispatch_tool, get_tools_for_agent
from services.adaptive_threshold import get_agent_calibration

AGENT_GOAL = (
    "Detect synthetic or fraudulent identities based on "
    "KTP match, face similarity, email age, name entropy, and geo-IP signals."
)

AGENT_STEP = "identity_risk_agent"
MAX_RETRIES = 3

SYSTEM_PROMPT = f"""
You are an Identity Risk Agent for a payment fraud detection system.
YOUR GOAL: {AGENT_GOAL}

RULES:
- Only use the features provided. Do not invent or assume missing data.
- If a feature is missing or unknown, treat it as neutral (0.5 for floats, false for booleans).
- Be precise. Return valid JSON only.

IMPORTANT:
- High name_entropy or name_ngram_entropy alone does NOT indicate risk if the name does not contain digits or symbols and other signals are normal.
- Only flag SUSPICIOUS_NAME if high entropy is combined with name_has_digits_or_symbols = true, or if high entropy is combined with other suspicious signals (e.g., new email, geo_ip_mismatch, negative sentiment).
- Do NOT flag common or multicultural names as suspicious based on entropy alone.

OUTPUT FORMAT (strict JSON, no extra text):
{{{{
  "risk": <float 0.0-1.0>,
  "confidence": <float 0.0-1.0>,
  "flags": [<list of triggered risk flags>],
  "explanation": "<1-2 sentence reasoning referencing only provided signals>",
  "agent_step": "identity_risk_agent"
}}}}

AVAILABLE FLAGS:
- KTP_MISMATCH, FACE_MISMATCH, NEW_EMAIL, NAME_VALIDATION,
  GEO_IP_MISMATCH, SUSPICIOUS_NAME, NEGATIVE_SENTIMENT
"""


def _build_rag_context() -> str:
    """Fetch historical identity assessments to augment the prompt (RAG)."""
    return fetch_agent_history(agent_step=AGENT_STEP, limit=3, min_confidence=0.6)


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
    INTER-AGENT COMMUNICATION (Fix 4):
    Read previous agent results from SessionState and inject as context.
    Identity runs first, so only session-level flags and errors are available here.
    """
    parts = []
    if state.flags:
        parts.append(f"\n--- UPSTREAM SESSION FLAGS ---\n  {state.flags}")
    if state.errors:
        parts.append(f"\n--- UPSTREAM ERRORS ---\n  {state.errors}")
    return "\n".join(parts)


def _build_user_prompt(features: IdentityInput, state: SessionState, rag_ctx: str) -> str:
    cal_ctx = _build_calibration_context()
    upstream_ctx = _build_upstream_context(state)
    tools = get_tools_for_agent(AGENT_STEP)
    tools_ctx = (
        f"\n--- AVAILABLE TOOLS ---\n"
        + "\n".join(f"  - {n}: {d}" for n, d in tools.items())
        if tools else ""
    )

    return f"""
Evaluate identity risk from these features:

- ktp_match_score: {features.ktp_match_score}
  (1.0 = perfect match, 0.0 = no match)
- face_similarity_score: {features.face_similarity_score}
  (1.0 = same person, 0.0 = different person)
- email_age_days: {features.email_age_days}
  (low = recently created email = suspicious)
- geo_ip_mismatch: {features.geo_ip_mismatch}
  (true = declared address doesn't match IP location)
- name_entropy: {features.name_entropy}
  (high + digits/symbols = suspicious, high alone is NOT suspicious)
- name_ngram_entropy: {features.name_ngram_entropy}
  (high = uncommon character sequences, only suspicious if combined with other flags)
- name_has_digits_or_symbols: {features.name_has_digits_or_symbols}
  (true = name contains digits or symbols = suspicious)
- entity_sentiment_score: {features.entity_sentiment_score}
  (0.0 = very negative public record, 1.0 = clean)
{rag_ctx}{cal_ctx}{upstream_ctx}{tools_ctx}

Return JSON only.
"""


def _build_corrective_prompt(
    features: IdentityInput, state: SessionState,
    rag_ctx: str, last_error: str, attempt: int
) -> str:
    """Build a retry prompt injecting the specific error from the previous attempt."""
    base = _build_user_prompt(features, state, rag_ctx)
    return f"""{base}

--- CORRECTIVE FEEDBACK (attempt {attempt}) ---
Your previous output was INVALID. The error was:
  "{last_error}"

FIX INSTRUCTIONS:
- Ensure your response is ONLY valid JSON (no markdown, no extra text).
- risk and confidence must be floats between 0.0 and 1.0.
- flags must be a JSON array of strings.
- agent_step must be "{AGENT_STEP}".
Return corrected JSON only.
"""


def _run_tool_enrichment(features: IdentityInput) -> None:
    """
    ACTION CAPABILITY (Fix 1) — call tools BEFORE the LLM to enrich features.
    Mutates features in-place with live-computed values.
    """
    # Tool: recompute name entropy signals using the dispatch layer
    shannon = dispatch_tool("shannon_entropy", name=str(getattr(features, "_raw_name", "")))
    if isinstance(shannon, float):
        features.name_entropy = shannon

    ngram = dispatch_tool("ngram_entropy", name=str(getattr(features, "_raw_name", "")))
    if isinstance(ngram, float):
        features.name_ngram_entropy = ngram


async def run_identity_agent(features: IdentityInput, state: SessionState) -> AgentResult:
    """
    Full Reason-Act Loop (async):
      Fix 1 — Tool dispatch BEFORE LLM call (enriches features)
      Fix 2 — RAG fetch BEFORE LLM, store AFTER success
      Fix 4 — Upstream SessionState context injected into prompt
      Corrective feedback on retry
      qwen_chat is blocking — offloaded to a thread via asyncio.to_thread()
    """
    state.transition(SessionStatus.AGENT_RUNNING, step=f"Running {AGENT_STEP}")

    # Fix 1: Tool dispatch — enrich features before building the prompt (sync, fast)
    _run_tool_enrichment(features)

    # Fix 2: RAG fetch — sync DB read, offload to thread to avoid blocking event loop
    rag_ctx = await asyncio.to_thread(_build_rag_context)

    # Build initial prompt (includes Fix 4: upstream context from state)
    user_prompt = _build_user_prompt(features, state, rag_ctx)
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # On retry, inject corrective feedback with the specific error
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

            # Fix 2: Store result to RAG history (sync DB write, offloaded)
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
            state.identity_result = result.model_dump()
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
    state.identity_result = fallback.model_dump()
    state.merge_flags(fallback.flags)
    return fallback
