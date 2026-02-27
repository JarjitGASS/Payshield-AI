from pydantic import BaseModel
from typing import Optional, Literal


class BehaviorAnalysis(BaseModel):
    classification: Literal["Human", "Bot"]
    confidence: float


class LoginResponse(BaseModel):
    success: bool
    message: str
    analysis: Optional[str] = None
