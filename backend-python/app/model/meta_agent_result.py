from pydantic import BaseModel

class MetaAgentResult(BaseModel):
    identity_risk: float
    behavior_risk: float
    network_risk: float
    overall_risk: float
    decision: str
    confidence: float
    explanation: str