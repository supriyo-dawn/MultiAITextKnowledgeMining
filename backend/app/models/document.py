"""
Document data models using Pydantic v2.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Document processing status."""

    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentMetadata(BaseModel):
    """Document metadata."""

    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type: pdf, docx, or txt")
    file_size_bytes: int = Field(..., description="File size in bytes")
    page_count: Optional[int] = Field(None, description="Number of pages (for PDFs)")
    character_count: int = Field(0, description="Total characters in extracted text")
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)


class Document(BaseModel):
    """Document model."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique document ID")
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED, description="Processing status")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    raw_text: Optional[str] = Field(None, description="Raw extracted text")
    error_message: Optional[str] = Field(None, description="Error details if processing failed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "COMPLETED",
                "metadata": {
                    "filename": "document.pdf",
                    "file_type": "pdf",
                    "file_size_bytes": 102400,
                    "page_count": 5,
                    "character_count": 15000,
                    "upload_timestamp": "2026-08-30T22:44:00Z",
                },
                "raw_text": "Document text content...",
                "error_message": None,
                "created_at": "2026-08-30T22:44:00Z",
                "updated_at": "2026-08-30T22:44:10Z",
            }
        }


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""

    document_id: str = Field(..., description="Unique document ID")
    filename: str = Field(..., description="Original filename")
    status: DocumentStatus = Field(..., description="Initial processing status")
    file_size_bytes: int = Field(..., description="File size in bytes")
    message: str = Field(default="Document uploaded successfully")


class DocumentListItem(BaseModel):
    """Item in document list."""

    id: str
    filename: str
    status: DocumentStatus
    file_size_bytes: int
    character_count: int
    upload_timestamp: datetime
    created_at: datetime


class DocumentDetail(BaseModel):
    """Detailed document information."""

    id: str
    status: DocumentStatus
    metadata: DocumentMetadata
    raw_text: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
