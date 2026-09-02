"""Unit tests for document service."""

import pytest

from app.models.document import DocumentStatus
from app.services.document_service import (
    create_document,
    delete_document,
    get_document,
    get_document_count,
    list_documents,
    DocumentServiceError,
)


@pytest.mark.asyncio
class TestDocumentService:
    """Tests for document service."""

    async def test_create_txt_document(self):
        """Test creating a document from TXT file."""
        content = "Hello, world!".encode("utf-8")

        doc = await create_document(
            filename="test.txt",
            file_content=content,
            file_type="txt",
            file_size=len(content),
        )

        assert doc.id is not None
        assert doc.metadata.filename == "test.txt"
        assert doc.metadata.file_type == "txt"
        assert doc.status == DocumentStatus.COMPLETED
        assert doc.raw_text == "Hello, world!"

        # Clean up
        await delete_document(doc.id)

    async def test_create_document_with_multiline_text(self):
        """Test creating document with multi-line text."""
        content = "Line 1\nLine 2\nLine 3".encode("utf-8")

        doc = await create_document(
            filename="test.txt",
            file_content=content,
            file_type="txt",
            file_size=len(content),
        )

        assert "Line 1" in doc.raw_text
        assert "Line 2" in doc.raw_text
        assert "Line 3" in doc.raw_text
        assert doc.metadata.character_count > 0

        # Clean up
        await delete_document(doc.id)

    async def test_get_document(self):
        """Test retrieving a document."""
        content = "Test content".encode("utf-8")

        doc1 = await create_document(
            filename="test.txt",
            file_content=content,
            file_type="txt",
            file_size=len(content),
        )

        # Retrieve document
        doc2 = await get_document(doc1.id)

        assert doc2 is not None
        assert doc2.id == doc1.id
        assert doc2.metadata.filename == "test.txt"

        # Clean up
        await delete_document(doc1.id)

    async def test_get_nonexistent_document(self):
        """Test retrieving non-existent document returns None."""
        doc = await get_document("nonexistent-id")
        assert doc is None

    async def test_list_documents(self):
        """Test listing documents."""
        # Create multiple documents
        docs = []
        for i in range(3):
            content = f"Content {i}".encode("utf-8")
            doc = await create_document(
                filename=f"test{i}.txt",
                file_content=content,
                file_type="txt",
                file_size=len(content),
            )
            docs.append(doc)

        # List documents
        listed, total = await list_documents(limit=10, offset=0)

        assert total >= 3
        assert len(listed) >= 3

        # Clean up
        for doc in docs:
            await delete_document(doc.id)

    async def test_list_documents_pagination(self):
        """Test document listing pagination."""
        # Create multiple documents
        docs = []
        for i in range(5):
            content = f"Content {i}".encode("utf-8")
            doc = await create_document(
                filename=f"test{i}.txt",
                file_content=content,
                file_type="txt",
                file_size=len(content),
            )
            docs.append(doc)

        # Get first page
        listed1, total = await list_documents(limit=2, offset=0)
        assert len(listed1) <= 2
        assert total >= 5

        # Get second page
        listed2, _ = await list_documents(limit=2, offset=2)
        assert len(listed2) <= 2

        # Documents should be different
        doc_ids1 = [d.id for d in listed1]
        doc_ids2 = [d.id for d in listed2]
        assert doc_ids1 != doc_ids2

        # Clean up
        for doc in docs:
            await delete_document(doc.id)

    async def test_delete_document(self):
        """Test deleting a document."""
        content = "Test content".encode("utf-8")

        doc = await create_document(
            filename="test.txt",
            file_content=content,
            file_type="txt",
            file_size=len(content),
        )

        doc_id = doc.id

        # Delete document
        deleted = await delete_document(doc_id)
        assert deleted is True

        # Verify it's gone
        retrieved = await get_document(doc_id)
        assert retrieved is None

    async def test_delete_nonexistent_document(self):
        """Test deleting non-existent document returns False."""
        deleted = await delete_document("nonexistent-id")
        assert deleted is False

    async def test_get_document_count(self):
        """Test getting document count."""
        initial_count = await get_document_count()

        # Create a document
        content = "Test".encode("utf-8")
        doc = await create_document(
            filename="test.txt",
            file_content=content,
            file_type="txt",
            file_size=len(content),
        )

        new_count = await get_document_count()
        assert new_count == initial_count + 1

        # Clean up
        await delete_document(doc.id)

    async def test_document_metadata_updated(self):
        """Test that document metadata is updated correctly."""
        content = "Test content with some words".encode("utf-8")

        doc = await create_document(
            filename="test.txt",
            file_content=content,
            file_type="txt",
            file_size=len(content),
        )

        assert doc.metadata.file_size_bytes == len(content)
        assert doc.metadata.character_count > 0
        assert doc.metadata.filename == "test.txt"
        assert doc.metadata.file_type == "txt"

        # Clean up
        await delete_document(doc.id)

    async def test_document_status_lifecycle(self):
        """Test document status changes during processing."""
        content = "Test content".encode("utf-8")

        # Create document (initially UPLOADED, then COMPLETED after processing)
        doc = await create_document(
            filename="test.txt",
            file_content=content,
            file_type="txt",
            file_size=len(content),
        )

        # Document should be COMPLETED after async processing
        assert doc.status == DocumentStatus.COMPLETED

        # Clean up
        await delete_document(doc.id)
