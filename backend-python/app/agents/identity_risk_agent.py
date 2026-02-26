import json
from model.agent_result import AgentResult
from model.input_schema import IdentityInput
from qwen.qwen import qwen_chat

SYSTEM_PROMPT = """
You are an Identity Risk Agent for a payment fraud detection system.
Analyze the provided identity signals and return a structured JSON risk assessment.

RULES:
- Only use the signals provided. Do not invent or assume missing data.
- If a signal is missing or unknown, treat it as neutral (0.5).
- Be precise. Return valid JSON only.

OUTPUT FORMAT (strict):
{
  "risk": <float 0.0-1.0>,
  "flags": [<list of triggered risk flags>],
  "explanation": "<1-2 sentence reasoning>",
  "confidence": <float 0.0-1.0>
}

AVAILABLE FLAGS:
- KTP_MISMATCH, FACE_MISMATCH, NEW_EMAIL, PHONE_REUSED,
  GEO_IP_MISMATCH, SUSPICIOUS_NAME, NEGATIVE_SENTIMENT
"""

def run_identity_agent(features: IdentityInput) -> AgentResult:
    user_prompt = f"""
Evaluate identity risk from these signals:

- ktp_match_score: {features.ktp_match_score}
  (1.0 = perfect match, 0.0 = no match)
- face_similarity_score: {features.face_similarity_score}
  (1.0 = same person, 0.0 = different person)
- email_age_days: {features.email_age_days}
  (low = recently created email = suspicious)
- phone_reuse_count: {features.phone_reuse_count}
  (>1 = phone shared across accounts = suspicious)
- geo_ip_mismatch: {features.geo_ip_mismatch}
  (true = declared address doesn't match IP location)
- name_entropy: {features.name_entropy}
  (high = random-looking name = suspicious)
- entity_sentiment_score: {features.entity_sentiment_score}
  (0.0 = very negative public record, 1.0 = clean)

Return JSON only.
"""
    raw = qwen_chat(SYSTEM_PROMPT, user_prompt)
    data = json.loads(raw)
    return AgentResult(**data)