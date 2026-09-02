"""
Document service for managing document storage and retrieval.
Uses in-memory storage for Phase 2; can be swapped for a database in Phase 6+.
"""

import logging
from datetime import datetime
from typing import Optional

from app.models.document import Document, DocumentMetadata, DocumentStatus
from app.services.text_extraction_service import extract_text, TextExtractionError
from app.utils.text import clean_text, get_text_statistics

logger = logging.getLogger(__name__)

# In-memory document store (Phase 2 only)
# TODO: Phase 6 - Replace with database (SQLAlchemy + PostgreSQL)
_documents_store: dict[str, Document] = {}


class DocumentServiceError(Exception):
    """Raised when document service operation fails."""

    pass


async def create_document(
    filename: str, file_content: bytes, file_type: str, file_size: int
) -> Document:
    """
    Create and store a new document.

    Args:
        filename: Original filename
        file_content: Raw file content
        file_type: File type ('pdf', 'docx', 'txt')
        file_size: File size in bytes

    Returns:
        Created Document object

    Raises:
        DocumentServiceError: If document creation fails
    """
    try:
        # Create metadata
        metadata = DocumentMetadata(
            filename=filename,
            file_type=file_type,
            file_size_bytes=file_size,
            page_count=None,  # Will be updated after extraction
            character_count=0,
        )

        # Create document
        document = Document(
            status=DocumentStatus.UPLOADED,
            metadata=metadata,
            raw_text=None,
        )

        # Store in memory
        _documents_store[document.id] = document

        logger.info(f"Created document {document.id}: {filename}")

        # Start text extraction (async in real implementation)
        await extract_document_text(document.id, file_content, file_type)

        return document

    except Exception as e:
        logger.error(f"Failed to create document: {e}")
        raise DocumentServiceError(f"Failed to create document: {str(e)}")


async def extract_document_text(
    document_id: str, file_content: bytes, file_type: str
) -> None:
    """
    Extract and clean text from document.

    Args:
        document_id: Document ID
        file_content: Raw file content
        file_type: File type ('pdf', 'docx', 'txt')
    """
    document = _documents_store.get(document_id)
    if not document:
        raise DocumentServiceError(f"Document {document_id} not found")

    try:
        document.status = DocumentStatus.PROCESSING
        document.updated_at = datetime.utcnow()

        # Extract text
        raw_text, page_count = extract_text(file_content, file_type)

        # Clean text
        cleaned_text = clean_text(raw_text)

        # Update document
        document.raw_text = cleaned_text
        document.metadata.character_count = len(cleaned_text)
        document.metadata.page_count = page_count
        document.status = DocumentStatus.COMPLETED
        document.updated_at = datetime.utcnow()

        logger.info(
            f"Successfully extracted text from document {document_id}: "
            f"{len(cleaned_text)} characters, {page_count or 'N/A'} pages"
        )

    except TextExtractionError as e:
        document.status = DocumentStatus.FAILED
        document.error_message = str(e)
        document.updated_at = datetime.utcnow()
        logger.error(f"Text extraction failed for document {document_id}: {e}")

    except Exception as e:
        document.status = DocumentStatus.FAILED
        document.error_message = f"Unexpected error: {str(e)}"
        document.updated_at = datetime.utcnow()
        logger.error(f"Unexpected error in document processing: {e}")


async def get_document(document_id: str) -> Optional[Document]:
    """
    Get document by ID.

    Args:
        document_id: Document ID

    Returns:
        Document object or None if not found
    """
    return _documents_store.get(document_id)


async def list_documents(
    limit: int = 100, offset: int = 0
) -> tuple[list[Document], int]:
    """
    List all documents with pagination.

    Args:
        limit: Maximum number of documents to return
        offset: Offset for pagination

    Returns:
        Tuple of (documents_list, total_count)
    """
    all_docs = list(_documents_store.values())

    # Sort by creation time (newest first)
    all_docs.sort(key=lambda d: d.created_at, reverse=True)

    total = len(all_docs)
    paginated = all_docs[offset : offset + limit]

    return paginated, total


async def delete_document(document_id: str) -> bool:
    """
    Delete a document.

    Args:
        document_id: Document ID

    Returns:
        True if deleted, False if not found
    """
    if document_id in _documents_store:
        del _documents_store[document_id]
        logger.info(f"Deleted document {document_id}")
        return True

    return False


async def get_document_count() -> int:
    """Get total number of documents."""
    return len(_documents_store)


async def get_documents_by_status(status: DocumentStatus) -> list[Document]:
    """Get all documents with a specific status."""
    return [d for d in _documents_store.values() if d.status == status]
