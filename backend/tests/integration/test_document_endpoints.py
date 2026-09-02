"""Integration tests for document endpoints."""

import io

import pytest
from docx import Document as DocxDocument
from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app())


class TestDocumentUploadEndpoint:
    """Tests for document upload endpoint."""

    def test_upload_txt_document(self):
        """Test uploading a TXT document."""
        content = b"Hello, world!"

        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", content, "text/plain")},
        )

        assert response.status_code == 200
        data = response.json()

        assert "document_id" in data
        assert data["filename"] == "test.txt"
        assert data["status"] == "COMPLETED"
        assert data["file_size_bytes"] == len(content)

    def test_upload_docx_document(self):
        """Test uploading a DOCX document."""
        # Create a simple DOCX file
        doc = DocxDocument()
        doc.add_paragraph("Test content")

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        content = buffer.read()

        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        )

        assert response.status_code == 200
        data = response.json()

        assert "document_id" in data
        assert data["filename"] == "test.docx"
        assert data["status"] == "COMPLETED"

    def test_upload_without_filename(self):
        """Test upload without filename fails."""
        response = client.post(
            "/api/documents/upload",
            files={"file": (None, b"content")},
        )

        assert response.status_code == 422  # FastAPI validation error

    def test_upload_unsupported_type(self):
        """Test uploading unsupported file type fails."""
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.jpg", b"fake image", "image/jpeg")},
        )

        assert response.status_code == 400

    def test_upload_wrong_signature(self):
        """Test uploading file with wrong signature fails."""
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", b"Not a PDF", "application/pdf")},
        )

        assert response.status_code == 400


class TestDocumentListEndpoint:
    """Tests for document listing endpoint."""

    def test_list_documents(self):
        """Test listing documents."""
        # Upload a document first
        content = b"Test content"
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", content)},
        )
        assert upload_response.status_code == 200

        # List documents
        response = client.get("/api/documents/")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_list_documents_pagination(self):
        """Test document listing with pagination."""
        response = client.get("/api/documents/?limit=5&offset=0")
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert len(data["items"]) <= 5


class TestDocumentDetailEndpoint:
    """Tests for document detail endpoint."""

    def test_get_document_detail(self):
        """Test getting document detail."""
        # Upload a document first
        content = b"Test content"
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", content)},
        )
        assert upload_response.status_code == 200
        doc_id = upload_response.json()["document_id"]

        # Get document detail
        response = client.get(f"/api/documents/{doc_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == doc_id
        assert data["status"] == "COMPLETED"
        assert data["raw_text"] is not None

    def test_get_nonexistent_document(self):
        """Test getting non-existent document returns 404."""
        response = client.get("/api/documents/nonexistent-id")
        assert response.status_code == 404


class TestDocumentStatusEndpoint:
    """Tests for document status endpoint."""

    def test_get_document_status(self):
        """Test getting document status."""
        # Upload a document
        content = b"Test content"
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", content)},
        )
        assert upload_response.status_code == 200
        doc_id = upload_response.json()["document_id"]

        # Get status
        response = client.get(f"/api/documents/{doc_id}/status")
        assert response.status_code == 200

        data = response.json()
        assert data["document_id"] == doc_id
        assert data["status"] in ["UPLOADED", "PROCESSING", "COMPLETED", "FAILED"]


class TestDocumentDeleteEndpoint:
    """Tests for document deletion endpoint."""

    def test_delete_document(self):
        """Test deleting a document."""
        # Upload a document
        content = b"Test content"
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", content)},
        )
        assert upload_response.status_code == 200
        doc_id = upload_response.json()["document_id"]

        # Delete document
        response = client.delete(f"/api/documents/{doc_id}")
        assert response.status_code == 200

        # Verify it's deleted
        response = client.get(f"/api/documents/{doc_id}")
        assert response.status_code == 404

    def test_delete_nonexistent_document(self):
        """Test deleting non-existent document returns 404."""
        response = client.delete("/api/documents/nonexistent-id")
        assert response.status_code == 404


class TestDocumentStatsEndpoint:
    """Tests for document statistics endpoint."""

    def test_get_document_stats(self):
        """Test getting document statistics."""
        response = client.get("/api/documents/stats/summary")
        assert response.status_code == 200

        data = response.json()
        assert "total_documents" in data
        assert data["total_documents"] >= 0
