import json
from model.agent_result import AgentResult
from model.meta_agent_result import MetaAgentResult
from qwen.qwen import qwen_chat

SYSTEM_PROMPT = """
You are a Meta-Agent Risk Orchestrator for a payment fraud detection system.
You receive outputs from 3 specialized agents and produce a final consolidated risk decision.

RULES:
- Only reason from the 3 agent outputs provided.
- Resolve conflicting signals intelligently.
- Do not invent data. Return valid JSON only.

DECISION GUIDE:
- overall_risk < 0.3  AND confidence >= 0.5 → APPROVE
- overall_risk 0.3-0.7 OR confidence < 0.5  → REVIEW
- overall_risk > 0.7  AND confidence >= 0.5 → REJECT

WEIGHTS (use as guidance):
- Identity risk:  45%
- Behavioral risk: 25%
- Network risk:   30%

OUTPUT FORMAT (strict):
{
  "identity_risk": <float 0.0-1.0>,
  "behavior_risk": <float 0.0-1.0>,
  "network_risk": <float 0.0-1.0>,
  "overall_risk": <float 0.0-1.0>,
  "decision": "APPROVE" | "REVIEW" | "REJECT",
  "confidence": <float 0.0-1.0>,
  "explanation": "<2-3 sentence consolidated reasoning>",
  "flags": [<all triggered flags combined>]
}
"""

def run_orchestrator(
    identity: AgentResult,
    behavioral: AgentResult,
    network: AgentResult
) -> MetaAgentResult:
    user_prompt = f"""
Consolidate these 3 agent outputs into a final risk decision:

IDENTITY AGENT:
- risk: {identity.risk}
- flags: {identity.flags}
- explanation: {identity.explanation}
- confidence: {identity.confidence}

BEHAVIORAL AGENT:
- risk: {behavioral.risk}
- flags: {behavioral.flags}
- explanation: {behavioral.explanation}
- confidence: {behavioral.confidence}

NETWORK AGENT:
- risk: {network.risk}
- flags: {network.flags}
- explanation: {network.explanation}
- confidence: {network.confidence}

Return the consolidated JSON decision only.
"""
    raw = qwen_chat(SYSTEM_PROMPT, user_prompt)
    data = json.loads(raw)
    return MetaAgentResult(**data)
    