import json
from model.agent_result import AgentResult
from model.input_schema import BehavioralInput
from qwen.qwen import qwen_chat

SYSTEM_PROMPT = """
You are a Behavioral Anomaly Agent for a payment fraud detection system.
Analyze behavioral biometric signals to detect bots, scripts, or suspicious human behavior.

RULES:
- Only use the signals provided. Do not invent or assume missing data.
- If a signal is missing or unknown, treat it as neutral (0.5).
- Return valid JSON only.

OUTPUT FORMAT (strict):
{
  "risk": <float 0.0-1.0>,
  "flags": [<list of triggered risk flags>],
  "explanation": "<1-2 sentence reasoning>",
  "confidence": <float 0.0-1.0>
}

AVAILABLE FLAGS:
- BOT_TYPING_PATTERN, ABNORMAL_MOUSE, TOO_FAST_SESSION,
  ODD_LOGIN_HOUR, UNUSUAL_NAVIGATION
"""

def run_behavioral_agent(features: BehavioralInput) -> AgentResult:
    user_prompt = f"""
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
    raw = qwen_chat(SYSTEM_PROMPT, user_prompt)
    data = json.loads(raw)
    return AgentResult(**data)