import json
from model.agent_result import AgentResult
from model.network_input import NetworkInput
from qwen.qwen import qwen_chat

SYSTEM_PROMPT = """
You are a Synthetic Network Agent for a payment fraud detection system.
Analyze network-level signals to detect synthetic identity clusters and mule account networks.

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
- DEVICE_SHARED_NETWORK, IP_CLUSTER, CROSS_MERCHANT_REUSE
"""

def run_network_agent(features: NetworkInput) -> AgentResult:
    user_prompt = f"""
Evaluate synthetic network risk from these signals:

- shared_device_count: {features.shared_device_count}
  (>1 = same device fingerprint on multiple accounts)
- shared_ip_count: {features.shared_ip_count}
  (>3 in 30 days = suspicious IP cluster)
- cross_merchant_reuse: {features.cross_merchant_reuse}
  (true = device/phone seen across different merchants)

Return JSON only.
"""
    raw = qwen_chat(SYSTEM_PROMPT, user_prompt)
    data = json.loads(raw)
    return AgentResult(**data)