"""
API routes for chunk operations.

Endpoints for creating, retrieving, and searching document chunks.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse

from app.models.chunk import (
    ChunkCreateRequest,
    ChunkListResponse,
    ChunkResponse,
    ChunkSearchQuery,
    ChunkSearchResponse,
    ChunkingStrategy,
)
from app.services.chunk_service import ChunkService
from app.services.chunking_service import TextChunker
from app.services.document_service import get_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chunks", tags=["chunks"])

# Initialize services
chunk_service = ChunkService()
text_chunker = TextChunker()


@router.get(
    "/",
    response_model=ChunkListResponse,
    summary="List all chunks",
    description="List chunks with pagination",
)
async def list_chunks(
    limit: int = Query(10, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Result offset"),
):
    """List all chunks with pagination."""
    try:
        chunks, total = await chunk_service.list_chunks(limit=limit, offset=offset)

        response_chunks = [
            ChunkResponse(
                id=chunk.id,
                document_id=chunk.document_id,
                text=chunk.text,
                metadata=chunk.metadata,
                created_at=chunk.created_at,
            )
            for chunk in chunks
        ]

        return ChunkListResponse(
            chunks=response_chunks,
            total_count=total,
            page=offset // limit if limit > 0 else 0,
            page_size=limit,
        )
    except Exception as e:
        logger.error(f"Error listing chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{chunk_id}",
    response_model=ChunkResponse,
    summary="Get chunk detail",
    description="Retrieve a specific chunk by ID",
)
async def get_chunk(chunk_id: str = Path(..., description="Chunk ID")):
    """Get a specific chunk by ID."""
    try:
        chunk = await chunk_service.get_chunk(chunk_id)

        if not chunk:
            raise HTTPException(status_code=404, detail=f"Chunk not found: {chunk_id}")

        return ChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            text=chunk.text,
            metadata=chunk.metadata,
            created_at=chunk.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chunk: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/document/{document_id}",
    response_model=ChunkListResponse,
    summary="List chunks for document",
    description="Get all chunks for a specific document",
)
async def get_document_chunks(
    document_id: str = Path(..., description="Document ID"),
    limit: int = Query(50, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Result offset"),
):
    """Get all chunks for a document."""
    try:
        # Verify document exists
        doc = await get_document(document_id)
        if not doc:
            raise HTTPException(
                status_code=404, detail=f"Document not found: {document_id}"
            )

        chunks, total = await chunk_service.get_chunks_by_document(
            document_id, limit=limit, offset=offset
        )

        response_chunks = [
            ChunkResponse(
                id=chunk.id,
                document_id=chunk.document_id,
                text=chunk.text,
                metadata=chunk.metadata,
                created_at=chunk.created_at,
            )
            for chunk in chunks
        ]

        return ChunkListResponse(
            chunks=response_chunks,
            total_count=total,
            page=offset // limit if limit > 0 else 0,
            page_size=limit,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/document/{document_id}/chunk",
    response_model=ChunkListResponse,
    summary="Chunk a document",
    description="Create chunks from a document's extracted text",
)
async def chunk_document(
    document_id: str = Path(..., description="Document ID"),
    request: ChunkCreateRequest = Body(...),
):
    """
    Chunk a document using the specified strategy.

    This endpoint triggers text chunking on an already-extracted document.
    The document must have completed text extraction.
    """
    try:
        # Verify document exists and has text
        doc = await get_document(document_id)
        if not doc:
            raise HTTPException(
                status_code=404, detail=f"Document not found: {document_id}"
            )

        if not doc.raw_text:
            raise HTTPException(
                status_code=400,
                detail=f"Document has no extracted text. Complete extraction first.",
            )

        # Delete previous chunks for this document
        deleted_count = await chunk_service.delete_document_chunks(document_id)
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} previous chunks for {document_id}")

        # Chunk the text
        chunk_dicts = text_chunker.chunk_text(
            text=doc.raw_text,
            document_id=document_id,
            strategy=request.strategy.value,
            section=None,  # Could be enhanced with document sections later
            preprocess=True,
            detect_language=request.detect_language,
            chunk_size=request.chunk_size or 512,
            overlap=request.overlap or 50,
        )

        # Store chunks
        created_chunks = []
        for chunk_dict in chunk_dicts:
            chunk = await chunk_service.create_chunk(
                document_id=chunk_dict["document_id"],
                text=chunk_dict["text"],
                start_position=chunk_dict["start_position"],
                end_position=chunk_dict["end_position"],
                sentence_count=chunk_dict.get("sentence_count", 1),
                section=chunk_dict.get("section"),
                paragraph_index=chunk_dict.get("paragraph_index"),
                quality_score=chunk_dict.get("quality_score", 0.0),
                language=chunk_dict.get("language"),
                is_normalized=chunk_dict.get("is_normalized", False),
                token_count=chunk_dict.get("token_count"),
                chunking_strategy=chunk_dict.get("chunking_strategy", "fixed_size"),
            )
            created_chunks.append(chunk)

        response_chunks = [
            ChunkResponse(
                id=chunk.id,
                document_id=chunk.document_id,
                text=chunk.text,
                metadata=chunk.metadata,
                created_at=chunk.created_at,
            )
            for chunk in created_chunks
        ]

        logger.info(
            f"Created {len(created_chunks)} chunks for document {document_id} "
            f"using strategy {request.strategy.value}"
        )

        return ChunkListResponse(
            chunks=response_chunks,
            total_count=len(created_chunks),
            page=0,
            page_size=len(created_chunks),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error chunking document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/search",
    response_model=ChunkSearchResponse,
    summary="Search chunks",
    description="Search chunks with text and metadata filters",
)
async def search_chunks(request: ChunkSearchQuery):
    """
    Search chunks with multiple filter options.

    Supports text search (substring match) and metadata filters
    (document, quality score, section, language).
    """
    try:
        import time

        start_time = time.time()

        results, total = await chunk_service.search_chunks(
            query=request.query,
            document_id=request.document_id,
            min_quality_score=request.min_quality_score,
            section=request.section,
            language=request.language,
            limit=request.limit,
            offset=request.offset,
        )

        query_time_ms = (time.time() - start_time) * 1000

        response_chunks = [
            ChunkResponse(
                id=chunk.id,
                document_id=chunk.document_id,
                text=chunk.text,
                metadata=chunk.metadata,
                created_at=chunk.created_at,
            )
            for chunk in results
        ]

        return ChunkSearchResponse(
            results=response_chunks,
            total_count=total,
            query_time_ms=query_time_ms,
        )

    except Exception as e:
        logger.error(f"Error searching chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/document/{document_id}/stats",
    summary="Get document chunk statistics",
    description="Get chunk statistics for a specific document",
)
async def get_document_chunk_stats(
    document_id: str = Path(..., description="Document ID")
):
    """Get chunk statistics for a document."""
    try:
        # Verify document exists
        doc = await get_document(document_id)
        if not doc:
            raise HTTPException(
                status_code=404, detail=f"Document not found: {document_id}"
            )

        stats = await chunk_service.get_statistics(document_id=document_id)

        return JSONResponse(content=stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chunk statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/stats/summary",
    summary="Get overall chunk statistics",
    description="Get statistics across all chunks",
)
async def get_chunk_stats():
    """Get overall chunk statistics."""
    try:
        stats = await chunk_service.get_statistics()

        return JSONResponse(content=stats)

    except Exception as e:
        logger.error(f"Error getting chunk statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
