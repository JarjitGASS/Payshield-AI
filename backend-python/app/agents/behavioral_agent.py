import json
from model.agent_result import AgentResult
from model.behavioral_input import BehavioralInput
from model.session_state import SessionState, SessionStatus
from qwen.qwen import qwen_chat

AGENT_GOAL = (
    "Detect bots, scripts, or suspicious human behavior "
    "using typing cadence, mouse entropy, session duration, login hour, "
    "and navigation consistency signals."
)

AGENT_STEP = "behavioral_agent"
MAX_RETRIES = 2

SYSTEM_PROMPT = f"""
You are a Behavioral Anomaly Agent for a payment fraud detection system.
YOUR GOAL: {AGENT_GOAL}

RULES:
- Only use the signals provided. Do not invent or assume missing data.
- If a signal is missing or unknown, treat it as neutral (0.5).
- Return valid JSON only.

OUTPUT FORMAT (strict JSON, no extra text):
{{
  "risk": <float 0.0-1.0>,
  "confidence": <float 0.0-1.0>,
  "flags": [<list of triggered risk flags>],
  "explanation": "<1-2 sentence reasoning referencing only provided signals>",
  "agent_step": "behavioral_agent"
}}

AVAILABLE FLAGS:
- BOT_TYPING_PATTERN, ABNORMAL_MOUSE, TOO_FAST_SESSION,
  ODD_LOGIN_HOUR, UNUSUAL_NAVIGATION
"""


def _build_user_prompt(features: BehavioralInput) -> str:
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

Return JSON only.
"""


def run_behavioral_agent(features: BehavioralInput, state: SessionState) -> AgentResult:
    state.transition(SessionStatus.AGENT_RUNNING, step=f"Running {AGENT_STEP}")

    user_prompt = _build_user_prompt(features)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = qwen_chat(SYSTEM_PROMPT, user_prompt)
            data = json.loads(raw)

            result = AgentResult(**data)

            if not (0.0 <= result.risk <= 1.0 and 0.0 <= result.confidence <= 1.0):
                raise ValueError(f"Score out of range: risk={result.risk}, confidence={result.confidence}")

            state.behavioral_result = result.model_dump()
            state.merge_flags(result.flags)
            return result

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            state.retry_count += 1
            error_msg = f"{AGENT_STEP} attempt {attempt} failed: {e}"
            state.errors.append(error_msg)
            print(f"[ReasonActLoop] {error_msg}. Retrying...")

    fallback = AgentResult(
        risk=0.5,
        confidence=0.0,
        flags=["AGENT_FAILURE"],
        explanation=f"{AGENT_STEP} failed to produce a valid output after {MAX_RETRIES} retries. Escalated to REVIEW.",
        agent_step=AGENT_STEP,
    )
    state.behavioral_result = fallback.model_dump()
    state.merge_flags(fallback.flags)
    return fallback
