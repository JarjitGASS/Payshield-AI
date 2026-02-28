"""
DTO for Human-in-the-Loop (HITL) review submission.

An analyst reviews a flagged session and provides:
  - rating:  "GOOD" (system decision was correct) or "BAD" (system decision was wrong)
  - decision: The analyst's override decision (APPROVE / REJECT)
  - note:    Free-text explanation of the analyst's reasoning
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ReviewRating(str, Enum):
    """Whether the AI system's original decision was correct or incorrect."""
    GOOD = "GOOD"   # AI decision was appropriate — no override needed
    BAD = "BAD"     # AI decision was wrong — analyst overrides


class OverrideDecision(str, Enum):
    """The analyst's final decision when overriding."""
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class HumanReviewInput(BaseModel):
    """
    Payload submitted by an analyst reviewing a REVIEW-flagged session.

    - If rating == GOOD: the AI's original decision stands, override_decision is optional.
    - If rating == BAD:  override_decision is required (APPROVE or REJECT).
    """
    session_id: str = Field(..., description="UUID of the session being reviewed")
    rating: ReviewRating = Field(..., description="GOOD = AI was correct, BAD = AI was wrong")
    override_decision: Optional[OverrideDecision] = Field(
        default=None,
        description="Required when rating is BAD. The analyst's corrected decision."
    )
    note: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="Analyst's reasoning for the review (5-2000 characters)"
    )


class HumanReviewResponse(BaseModel):
    """Response after successfully storing a human review."""
    status: str = "ok"
    session_id: str
    applied_decision: str = Field(..., description="The final decision after HITL review")
    message: str
