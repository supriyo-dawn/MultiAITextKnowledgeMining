"""Knowledge extraction models."""

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class Entity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    text: str
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    start_position: int
    end_position: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Relationship(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    document_id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str = "CO_OCCURS_WITH"
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
