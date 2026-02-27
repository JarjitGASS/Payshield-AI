import json
from model.agent_result import AgentResult
from model.network_input import NetworkInput
from model.session_state import SessionState, SessionStatus
from qwen.qwen import qwen_chat

AGENT_GOAL = (
    "Detect synthetic identity clusters and mule account networks "
    "using shared device, shared IP, account age, and cross-merchant reuse signals."
)

AGENT_STEP = "synthetic_network_agent"
MAX_RETRIES = 2

SYSTEM_PROMPT = f"""
You are a Synthetic Network Agent for a payment fraud detection system.
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
  "agent_step": "synthetic_network_agent"
}}

AVAILABLE FLAGS:
- DEVICE_SHARED_NETWORK, IP_CLUSTER, CROSS_MERCHANT_REUSE,
  RAPID_ACCOUNT_CREATION
"""


def _build_user_prompt(features: NetworkInput) -> str:
    return f"""
Evaluate synthetic network risk from these signals:

- shared_device_count: {features.shared_device_count}
  (>1 = same device fingerprint on multiple accounts)
- shared_ip_count: {features.shared_ip_count}
  (>3 in 30 days = suspicious IP cluster)
- cross_merchant_reuse: {features.cross_merchant_reuse}
  (true = device/phone seen across different merchants)

Return JSON only.
"""


def run_network_agent(features: NetworkInput, state: SessionState) -> AgentResult:
    state.transition(SessionStatus.AGENT_RUNNING, step=f"Running {AGENT_STEP}")

    user_prompt = _build_user_prompt(features)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = qwen_chat(SYSTEM_PROMPT, user_prompt)
            data = json.loads(raw)

            result = AgentResult(**data)

            if not (0.0 <= result.risk <= 1.0 and 0.0 <= result.confidence <= 1.0):
                raise ValueError(f"Score out of range: risk={result.risk}, confidence={result.confidence}")

            state.network_result = result.model_dump()
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
    state.network_result = fallback.model_dump()
    state.merge_flags(fallback.flags)
    return fallback
