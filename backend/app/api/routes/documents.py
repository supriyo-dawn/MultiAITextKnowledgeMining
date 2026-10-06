"""API routes for document upload and management."""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Body, File, HTTPException, Query, UploadFile

from app.core.config import settings
from app.models.chunk import ChunkCreateRequest, ChunkListResponse
from app.models.document import (
    DocumentDetail,
    DocumentListItem,
    DocumentStatus,
    DocumentUploadResponse,
)
from app.services.document_service import (
    create_document,
    delete_document,
    get_document,
    get_document_count,
    list_documents,
)
from app.utils.file import FileValidationError, validate_file_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("/")
async def list_all_documents(
    limit: Annotated[int, Query(ge=1, le=1000)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List all uploaded documents with pagination."""
    try:
        documents, total = await list_documents(limit=limit, offset=offset)

        # Convert to list items
        items = [
            DocumentListItem(
                id=doc.id,
                filename=doc.metadata.filename,
                status=doc.status,
                file_size_bytes=doc.metadata.file_size_bytes,
                character_count=doc.metadata.character_count,
                upload_timestamp=doc.metadata.upload_timestamp,
                created_at=doc.created_at,
            )
            for doc in documents
        ]

        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a new document (PDF, DOCX, TXT).

    - **file**: Document file (max {MAX_UPLOAD_SIZE_MB} MB)
    - Returns: document_id for tracking processing status
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")

    try:
        # Read file content
        content = await file.read()

        # Validate file
        file_type, file_size = validate_file_upload(
            file.filename,
            content,
            allowed_types=settings.ALLOWED_FILE_TYPES,
        )

        # Create document (starts processing)
        document = await create_document(
            filename=file.filename,
            file_content=content,
            file_type=file_type,
            file_size=file_size,
        )

        logger.info(
            f"Document uploaded: {document.id} ({file.filename}, {file_size} bytes)"
        )

        return DocumentUploadResponse(
            document_id=document.id,
            filename=document.metadata.filename,
            status=document.status,
            file_size_bytes=document.metadata.file_size_bytes,
            message="Document uploaded successfully",
        )

    except FileValidationError as e:
        logger.warning(f"File validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document_detail(document_id: str):
    """Get document details including extracted text."""
    try:
        document = await get_document(document_id)

        if not document:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

        return DocumentDetail(
            id=document.id,
            status=document.status,
            metadata=document.metadata,
            raw_text=document.raw_text,
            error_message=document.error_message,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document")


@router.get("/{document_id}/status")
async def get_document_status(document_id: str):
    """Get document processing status."""
    try:
        document = await get_document(document_id)

        if not document:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

        return {
            "document_id": document.id,
            "filename": document.metadata.filename,
            "status": document.status,
            "character_count": document.metadata.character_count,
            "page_count": document.metadata.page_count,
            "error_message": document.error_message,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve status")


@router.delete("/{document_id}")
async def delete_document_by_id(document_id: str):
    """Delete a document."""
    try:
        deleted = await delete_document(document_id)

        if not deleted:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

        logger.info(f"Document deleted: {document_id}")

        return {"message": f"Document {document_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.get("/stats/summary")
async def get_document_stats():
    """Get document statistics."""
    try:
        total = await get_document_count()

        return {
            "total_documents": total,
            "api_version": "0.1.0",
        }

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.post(
    "/{document_id}/chunk",
    response_model=ChunkListResponse,
    summary="Chunk a document",
    description="Create chunks from a document's extracted text",
)
async def chunk_document_endpoint(
    document_id: str,
    request: ChunkCreateRequest = Body(...),
):
    """Trigger chunking on an uploaded document."""
    from app.api.routes.chunks import chunk_document
    return await chunk_document(document_id=document_id, request=request)

