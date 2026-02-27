from pydantic import BaseModel, Field
from typing import List

class MetaAgentResult(BaseModel):
    identity_risk: float = Field(..., ge=0.0, le=1.0)
    behavior_risk: float = Field(..., ge=0.0, le=1.0)
    network_risk: float = Field(..., ge=0.0, le=1.0)
    overall_risk: float = Field(..., ge=0.0, le=1.0)
    decision: str = Field(..., description="APPROVE | REVIEW | REJECT")
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: str = Field(..., description="2-3 sentence consolidated reasoning")
    flags: List[str] = Field(default_factory=list, description="All triggered flags from all agents")