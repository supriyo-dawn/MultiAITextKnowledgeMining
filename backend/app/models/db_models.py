"""
SQLAlchemy ORM models for persistent database storage.

These map directly to database tables. The existing Pydantic models
in document.py and chunk.py remain the API layer — conversion
functions translate between ORM ↔ Pydantic.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentDB(Base):
    """SQLAlchemy model for documents table."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    status = Column(String, nullable=False, default="UPLOADED")
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    page_count = Column(Integer, nullable=True)
    character_count = Column(Integer, default=0)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    raw_text = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship: one document has many chunks
    chunks = relationship("ChunkDB", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DocumentDB id={self.id} filename={self.filename} status={self.status}>"


class ChunkDB(Base):
    """SQLAlchemy model for chunks table."""

    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)

    # Position metadata
    start_position = Column(Integer, default=0)
    end_position = Column(Integer, default=0)
    section = Column(String, nullable=True)
    paragraph_index = Column(Integer, nullable=True)

    # Quality metadata
    sentence_count = Column(Integer, default=1)
    quality_score = Column(Float, default=0.0)
    quality_level = Column(String, default="medium")

    # Language & processing metadata
    language = Column(String, nullable=True)
    is_normalized = Column(Boolean, default=False)
    token_count = Column(Integer, nullable=True)
    chunking_strategy = Column(String, default="fixed_size")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to document
    document = relationship("DocumentDB", back_populates="chunks")

    def __repr__(self):
        return f"<ChunkDB id={self.id} doc={self.document_id} len={len(self.text) if self.text else 0}>"
