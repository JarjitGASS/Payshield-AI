import json
from model.agent_result import AgentResult
from model.identity_input import IdentityInput
from model.session_state import SessionState, SessionStatus
from qwen.qwen import qwen_chat

AGENT_GOAL = (
    "Detect synthetic or fraudulent identities based on "
    "KTP match, face similarity, email age, name entropy, and geo-IP signals."
)

AGENT_STEP = "identity_risk_agent"
MAX_RETRIES = 2

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
{{
  "risk": <float 0.0-1.0>,
  "confidence": <float 0.0-1.0>,
  "flags": [<list of triggered risk flags>],
  "explanation": "<1-2 sentence reasoning referencing only provided signals>",
  "agent_step": "identity_risk_agent"
}}

AVAILABLE FLAGS:
- KTP_MISMATCH, FACE_MISMATCH, NEW_EMAIL, NAME_VALIDATION,
  GEO_IP_MISMATCH, SUSPICIOUS_NAME, NEGATIVE_SENTIMENT
"""


def _build_user_prompt(features: IdentityInput) -> str:
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

Return JSON only.
"""


def run_identity_agent(features: IdentityInput, state: SessionState) -> AgentResult:
    # Update session state: agent is now running
    state.transition(SessionStatus.AGENT_RUNNING, step=f"Running {AGENT_STEP}")

    user_prompt = _build_user_prompt(features)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = qwen_chat(SYSTEM_PROMPT, user_prompt)
            data = json.loads(raw)

            # Structured output validation
            result = AgentResult(**data)

            # Validate score ranges
            if not (0.0 <= result.risk <= 1.0 and 0.0 <= result.confidence <= 1.0):
                raise ValueError(f"Score out of range: risk={result.risk}, confidence={result.confidence}")

            # Store result in session state
            state.identity_result = result.model_dump()
            state.merge_flags(result.flags)
            return result

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            state.retry_count += 1
            error_msg = f"{AGENT_STEP} attempt {attempt} failed: {e}"
            state.errors.append(error_msg)
            print(f"[ReasonActLoop] {error_msg}. Retrying...")

    # All retries exhausted — return safe fallback
    fallback = AgentResult(
        risk=0.5,
        confidence=0.0,
        flags=["AGENT_FAILURE"],
        explanation=f"{AGENT_STEP} failed to produce a valid output after {MAX_RETRIES} retries. Escalated to REVIEW.",
        agent_step=AGENT_STEP,
    )
    state.identity_result = fallback.model_dump()
    state.merge_flags(fallback.flags)
    return fallback
