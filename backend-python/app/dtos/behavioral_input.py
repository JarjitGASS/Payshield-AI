from pydantic import BaseModel
from typing import List, Optional

class BehavioralInput(BaseModel):
    typing_cadence_variance: float
    mouse_entropy_score: float
    session_duration_sec: int
    login_hour: int
    navigation_consistency_score: float