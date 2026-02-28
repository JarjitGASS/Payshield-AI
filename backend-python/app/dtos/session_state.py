from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class SessionStatus(str, Enum):
    PENDING = "PENDING"                   # Session created, not yet started
    PREPROCESSING = "PREPROCESSING"       # Tools running (OCR, face match, entropy)
    AGENT_RUNNING = "AGENT_RUNNING"       # Individual agents executing
    ORCHESTRATING = "ORCHESTRATING"       # Meta-agent consolidating results
    GUARDRAIL_CHECK = "GUARDRAIL_CHECK"   # Policy validation in progress
    COMPLETE = "COMPLETE"                 # Final decision produced: APPROVE or REJECT
    REVIEW = "REVIEW"                     # Escalated to human analyst
    ERROR = "ERROR"                       # Unrecoverable failure


class SessionState(BaseModel):
    """
    Tracks the full state of a risk assessment session throughout
    the agentic workflow. Passed through every agent and updated
    at each step, enabling the Reason-Act loop.
    """
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(default=None, description="User ID being assessed")
    status: SessionStatus = Field(default=SessionStatus.PENDING, description="Current workflow stage")
    current_step: str = Field(default="", description="Human-readable current agent step")
    retry_count: int = Field(default=0, description="Number of retries attempted in reason-act loop")

    # Agent outputs (populated progressively as workflow advances)
    identity_result: Optional[dict] = Field(default=None, description="Output from identity risk agent")
    behavioral_result: Optional[dict] = Field(default=None, description="Output from behavioral agent")
    network_result: Optional[dict] = Field(default=None, description="Output from network agent")
    meta_result: Optional[dict] = Field(default=None, description="Output from meta-agent orchestrator")

    # Final decision
    final_decision: Optional[str] = Field(default=None, description="APPROVE | REVIEW | REJECT")
    final_overall_risk: Optional[float] = Field(default=None, description="Final computed overall risk score")

    # Audit trail
    flags: List[str] = Field(default_factory=list, description="All flags triggered across agents")
    errors: List[str] = Field(default_factory=list, description="Errors encountered during processing")

    def transition(self, new_status: SessionStatus, step: str = "") -> None:
        """Advance the session state to the next stage."""
        self.status = new_status
        if step:
            self.current_step = step

    def record_error(self, error: str) -> None:
        """Log an error and transition to ERROR state."""
        self.errors.append(error)
        self.status = SessionStatus.ERROR
        self.current_step = f"ERROR: {error}"

    def merge_flags(self, new_flags: List[str]) -> None:
        """Accumulate flags from all agents into the session."""
        for flag in new_flags:
            if flag not in self.flags:
                self.flags.append(flag)
