"""
Chunk data models for text chunking.

This module defines Pydantic v2 models for chunks created from documents,
including metadata enrichment (position, quality scoring, section tracking).
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ChunkingStrategy(str, Enum):
    """Supported text chunking strategies."""

    FIXED_SIZE = "fixed_size"
    SEMANTIC_SENTENCE = "semantic_sentence"
    SLIDING_WINDOW = "sliding_window"


class ChunkQualityLevel(str, Enum):
    """Quality levels for chunks based on scoring."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ChunkMetadata(BaseModel):
    """Metadata enrichment for chunks."""

    document_id: str = Field(..., description="Parent document ID")
    start_position: int = Field(..., description="Character offset in original text")
    end_position: int = Field(..., description="Character offset in original text")
    section: Optional[str] = Field(None, description="Document section/heading")
    paragraph_index: Optional[int] = Field(None, description="Paragraph number in document")
    sentence_count: int = Field(default=1, description="Number of sentences in chunk")
    quality_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Quality score 0-1"
    )
    quality_level: ChunkQualityLevel = Field(
        default=ChunkQualityLevel.MEDIUM, description="Quality level label"
    )
    language: Optional[str] = Field(None, description="Detected language code (ISO 639-1)")
    is_normalized: bool = Field(default=False, description="Whether text was normalized")
    token_count: Optional[int] = Field(None, description="Estimated token count")
    chunking_strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.FIXED_SIZE, description="Strategy used to create chunk"
    )


class Chunk(BaseModel):
    """Represents a text chunk with enriched metadata."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique chunk ID")
    document_id: str = Field(..., description="Parent document ID")
    text: str = Field(..., description="Chunk text content")
    metadata: ChunkMetadata = Field(..., description="Enriched chunk metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")

    class Config:
        """Pydantic config for Chunk model."""

        json_schema_extra = {
            "example": {
                "id": "chunk-123",
                "document_id": "doc-456",
                "text": "This is a sample chunk of text.",
                "metadata": {
                    "document_id": "doc-456",
                    "start_position": 100,
                    "end_position": 130,
                    "section": "Introduction",
                    "paragraph_index": 2,
                    "sentence_count": 1,
                    "quality_score": 0.85,
                    "quality_level": "high",
                    "language": "en",
                    "is_normalized": True,
                    "token_count": 8,
                    "chunking_strategy": "fixed_size",
                },
            }
        }


# API Response Models


class ChunkCreateRequest(BaseModel):
    """Request to chunk a document."""

    document_id: str = Field(..., description="Document ID to chunk")
    strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.FIXED_SIZE, description="Chunking strategy"
    )
    chunk_size: Optional[int] = Field(
        default=512, description="Chunk size (for fixed-size strategy)"
    )
    overlap: Optional[int] = Field(
        default=50, description="Overlap between chunks (for sliding window)"
    )
    detect_language: bool = Field(
        default=True, description="Whether to detect language"
    )


class ChunkResponse(BaseModel):
    """Response model for a single chunk."""

    id: str
    document_id: str
    text: str
    metadata: ChunkMetadata
    created_at: datetime


class ChunkListResponse(BaseModel):
    """Response model for list of chunks."""

    chunks: list[ChunkResponse]
    total_count: int
    page: int
    page_size: int


class ChunkSearchQuery(BaseModel):
    """Query model for chunk search."""

    query: Optional[str] = Field(None, description="Text search query")
    document_id: Optional[str] = Field(None, description="Filter by document ID")
    min_quality_score: Optional[float] = Field(
        None, description="Minimum quality score filter"
    )
    section: Optional[str] = Field(None, description="Filter by section")
    language: Optional[str] = Field(None, description="Filter by language")
    limit: int = Field(default=10, le=100, description="Result limit")
    offset: int = Field(default=0, description="Result offset")


class ChunkSearchResponse(BaseModel):
    """Response for chunk search results."""

    results: list[ChunkResponse]
    total_count: int
    query_time_ms: float
