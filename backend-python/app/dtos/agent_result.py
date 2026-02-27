from pydantic import BaseModel, Field
from typing import List

class AgentResult(BaseModel):
    risk: float = Field(..., ge=0.0, le=1.0, description="Risk score between 0.0 (safe) and 1.0 (high risk)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Agent confidence in its assessment")
    flags: List[str] = Field(default_factory=list, description="Triggered risk flags")
    explanation: str = Field(..., description="1-2 sentence reasoning referencing only provided signals")
    agent_step: str = Field(default="", description="Which agent produced this result")
