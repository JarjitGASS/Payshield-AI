"""
RAG History Table — stores every completed agent assessment for retrieval-augmented generation.
Agents query this table before each LLM call to find similar historical cases,
grounding their reasoning in real past decisions.
"""
import datetime
from database.database import Base
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid


class AgentHistory(Base):
    """
    Stores individual agent outputs (identity, behavioral, network) for RAG retrieval.
    """
    __tablename__ = "agent_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, index=True, nullable=False)
    agent_step = Column(String, index=True, nullable=False)       # identity_risk_agent | behavioral_agent | synthetic_network_agent
    input_features = Column(JSON, nullable=False)                  # Raw input features sent to agent
    risk = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    flags = Column(JSON, default=[])
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class OrchestratorHistory(Base):
    """
    Stores meta-agent orchestrator outputs and final decisions for RAG retrieval and adaptive thresholds.
    """
    __tablename__ = "orchestrator_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, unique=True, index=True, nullable=False)
    identity_risk = Column(Float, nullable=False)
    behavior_risk = Column(Float, nullable=False)
    network_risk = Column(Float, nullable=False)
    overall_risk = Column(Float, nullable=False)
    decision = Column(String, index=True, nullable=False)         # APPROVE | REVIEW | REJECT
    confidence = Column(Float, nullable=False)
    explanation = Column(Text, nullable=False)
    flags = Column(JSON, default=[])

    # Human-in-the-loop override (nullable until analyst acts)
    human_override_decision = Column(String, nullable=True)       # APPROVE | REJECT | None
    human_override_note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.datetime.utcnow)
