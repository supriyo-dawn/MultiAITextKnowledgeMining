"""
Document service for managing document storage and retrieval.

Phase A: Uses SQLite via SQLAlchemy for persistent storage.
Previously used an in-memory dictionary (Phase 2).
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select

from app.core.database import async_session_factory
from app.models.db_models import DocumentDB
from app.models.document import Document, DocumentMetadata, DocumentStatus
from app.services.text_extraction_service import TextExtractionError, extract_text
from app.utils.text import clean_text

logger = logging.getLogger(__name__)


class DocumentServiceError(Exception):
    """Raised when document service operation fails."""
    pass


# ── Conversion helpers ──────────────────────────────────────────

def _db_to_pydantic(db_doc: DocumentDB) -> Document:
    """Convert a SQLAlchemy DocumentDB row to a Pydantic Document."""
    return Document(
        id=db_doc.id,
        status=DocumentStatus(db_doc.status),
        metadata=DocumentMetadata(
            filename=db_doc.filename,
            file_type=db_doc.file_type,
            file_size_bytes=db_doc.file_size_bytes,
            page_count=db_doc.page_count,
            character_count=db_doc.character_count,
            upload_timestamp=db_doc.upload_timestamp,
        ),
        raw_text=db_doc.raw_text,
        error_message=db_doc.error_message,
        created_at=db_doc.created_at,
        updated_at=db_doc.updated_at,
    )


# ── Public service functions ────────────────────────────────────

async def create_document(
    filename: str, file_content: bytes, file_type: str, file_size: int
) -> Document:
    """
    Create and store a new document.

    Workflow:
    1. Insert a row with status=UPLOADED
    2. Extract text from the file bytes
    3. Clean the extracted text
    4. Update the row with the result (or error)

    Args:
        filename: Original filename
        file_content: Raw file content
        file_type: File type ('pdf', 'docx', 'txt')
        file_size: File size in bytes

    Returns:
        Created Document object
    """
    try:
        async with async_session_factory() as session:
            db_doc = DocumentDB(
                filename=filename,
                file_type=file_type,
                file_size_bytes=file_size,
                status=DocumentStatus.UPLOADED.value,
            )
            session.add(db_doc)
            await session.commit()
            await session.refresh(db_doc)

            logger.info(f"Created document {db_doc.id}: {filename}")

            # Run text extraction
            await _extract_document_text(session, db_doc, file_content, file_type)

            return _db_to_pydantic(db_doc)

    except Exception as e:
        logger.error(f"Failed to create document: {e}")
        raise DocumentServiceError(f"Failed to create document: {str(e)}")


async def _extract_document_text(
    session, db_doc: DocumentDB, file_content: bytes, file_type: str
) -> None:
    """Extract text from file content and update the document row."""
    try:
        db_doc.status = DocumentStatus.PROCESSING.value
        await session.commit()

        # Extract text
        raw_text, page_count = extract_text(file_content, file_type)

        # Clean text
        cleaned_text = clean_text(raw_text)

        # Update document with results
        db_doc.raw_text = cleaned_text
        db_doc.character_count = len(cleaned_text)
        db_doc.page_count = page_count
        db_doc.status = DocumentStatus.COMPLETED.value
        db_doc.updated_at = datetime.utcnow()
        await session.commit()

        logger.info(
            f"Extracted text from {db_doc.id}: "
            f"{len(cleaned_text)} chars, {page_count or 'N/A'} pages"
        )

    except TextExtractionError as e:
        db_doc.status = DocumentStatus.FAILED.value
        db_doc.error_message = str(e)
        db_doc.updated_at = datetime.utcnow()
        await session.commit()
        logger.error(f"Text extraction failed for {db_doc.id}: {e}")

    except Exception as e:
        db_doc.status = DocumentStatus.FAILED.value
        db_doc.error_message = f"Unexpected error: {str(e)}"
        db_doc.updated_at = datetime.utcnow()
        await session.commit()
        logger.error(f"Unexpected error processing {db_doc.id}: {e}")


async def get_document(document_id: str) -> Optional[Document]:
    """Get document by ID."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(DocumentDB).where(DocumentDB.id == document_id)
        )
        db_doc = result.scalar_one_or_none()
        return _db_to_pydantic(db_doc) if db_doc else None


async def list_documents(
    limit: int = 100, offset: int = 0
) -> tuple[list[Document], int]:
    """List all documents with pagination, newest first."""
    async with async_session_factory() as session:
        # Total count
        count_result = await session.execute(select(func.count(DocumentDB.id)))
        total = count_result.scalar() or 0

        # Paginated results
        result = await session.execute(
            select(DocumentDB)
            .order_by(DocumentDB.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        db_docs = result.scalars().all()

        return [_db_to_pydantic(d) for d in db_docs], total


async def delete_document(document_id: str) -> bool:
    """Delete a document and its chunks (cascade)."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(DocumentDB).where(DocumentDB.id == document_id)
        )
        db_doc = result.scalar_one_or_none()

        if not db_doc:
            return False

        await session.delete(db_doc)
        await session.commit()
        logger.info(f"Deleted document {document_id}")
        return True


async def get_document_count() -> int:
    """Get total number of documents."""
    async with async_session_factory() as session:
        result = await session.execute(select(func.count(DocumentDB.id)))
        return result.scalar() or 0


async def get_documents_by_status(status: DocumentStatus) -> list[Document]:
    """Get all documents with a specific status."""
    async with async_session_factory() as session:
        result = await session.execute(
            select(DocumentDB).where(DocumentDB.status == status.value)
        )
        db_docs = result.scalars().all()
        return [_db_to_pydantic(d) for d in db_docs]
