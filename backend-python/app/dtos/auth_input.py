from pydantic import BaseModel
from typing import List, Any, Optional


class InteractionEvent(BaseModel):
    t: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None
    key: Optional[str] = None
    type: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str
    behavior: List[Any]
