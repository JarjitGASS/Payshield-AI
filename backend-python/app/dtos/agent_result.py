from pydantic import BaseModel

class AgentResult(BaseModel):
    risk: float
    explanation: str
