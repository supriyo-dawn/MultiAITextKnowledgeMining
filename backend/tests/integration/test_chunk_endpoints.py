"""
Integration tests for chunk API endpoints.

Tests all chunk endpoints with realistic request/response scenarios.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.chunk_service import ChunkService
from app.services.document_service import create_document


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_document(client):
    """Create a sample document with extracted text through API."""
    test_content = """This is the introduction section. It contains basic information about the topic.
It has multiple sentences for testing the chunking algorithms.

This is the main body section. It discusses various aspects of the subject matter.
Each paragraph contains related information that should be kept together.
The chunking strategy should respect these logical boundaries.

This is the conclusion section. It summarizes the key points made earlier.
The final section often contains important takeaways for the reader."""
    
    # Create document through API
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", test_content.encode("utf-8"))},
    )
    assert response.status_code == 200
    doc_data = response.json()
    
    # Fetch the document to get the full object
    doc_response = client.get(f"/api/documents/{doc_data['document_id']}")
    assert doc_response.status_code == 200
    
    from app.services.document_service import get_document
    import asyncio
    doc = asyncio.run(get_document(doc_data['document_id']))
    return doc


class TestListChunksEndpoint:
    """Tests for GET /api/chunks endpoint."""

    @pytest.mark.asyncio
    async def test_list_chunks_empty(self, client):
        """Test listing chunks when none exist."""
        response = client.get("/api/chunks/")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0
        assert data["chunks"] == []
        assert data["page"] == 0
        assert data["page_size"] == 10

    @pytest.mark.asyncio
    async def test_list_chunks_pagination(self, client, sample_document):
        """Test pagination of chunk listing."""
        # First create chunks
        chunk_response = client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )
        assert chunk_response.status_code == 200

        # Test first page
        response = client.get("/api/chunks/?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["chunks"]) <= 2
        assert data["page"] == 0

    @pytest.mark.asyncio
    async def test_list_chunks_with_limit(self, client, sample_document):
        """Test chunk listing with custom limit."""
        # Create chunks first
        client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )

        response = client.get("/api/chunks/?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] == 5


class TestGetChunkEndpoint:
    """Tests for GET /api/chunks/{chunk_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_chunk_detail(self, client, sample_document):
        """Test getting a specific chunk by ID."""
        # Create chunks
        chunk_response = client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )
        assert chunk_response.status_code == 200

        chunks_data = chunk_response.json()
        if chunks_data["chunks"]:
            chunk_id = chunks_data["chunks"][0]["id"]

            # Get the chunk
            response = client.get(f"/api/chunks/{chunk_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == chunk_id
            assert "text" in data
            assert "metadata" in data
            assert data["metadata"]["document_id"] == sample_document.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_chunk(self, client):
        """Test getting nonexistent chunk returns 404."""
        response = client.get("/api/chunks/nonexistent-id")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestGetDocumentChunksEndpoint:
    """Tests for GET /api/chunks/document/{document_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_chunks_for_document(self, client, sample_document):
        """Test getting all chunks for a document."""
        # Create chunks
        chunk_response = client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )
        assert chunk_response.status_code == 200

        # Get chunks
        response = client.get(f"/api/chunks/document/{sample_document.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] > 0
        assert all(c["document_id"] == sample_document.id for c in data["chunks"])

    @pytest.mark.asyncio
    async def test_get_chunks_for_nonexistent_document(self, client):
        """Test getting chunks for nonexistent document returns 404."""
        response = client.get("/api/chunks/document/nonexistent-doc-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_document_chunks_pagination(self, client, sample_document):
        """Test pagination when getting document chunks."""
        # Create chunks
        client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )

        response = client.get(
            f"/api/chunks/document/{sample_document.id}?limit=2&offset=0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] == 2


class TestChunkDocumentEndpoint:
    """Tests for POST /api/documents/{document_id}/chunk endpoint."""

    @pytest.mark.asyncio
    async def test_chunk_document_fixed_size(self, client, sample_document):
        """Test chunking a document with fixed-size strategy."""
        response = client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={
                "document_id": sample_document.id,
                "strategy": "fixed_size",
                "chunk_size": 256,
                "overlap": 50,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] > 0
        assert all(c["text"] for c in data["chunks"])
        assert all(
            c["metadata"]["chunking_strategy"] == "fixed_size" for c in data["chunks"]
        )

    @pytest.mark.asyncio
    async def test_chunk_document_semantic_sentence(self, client, sample_document):
        """Test chunking a document with semantic sentence strategy."""
        response = client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={
                "document_id": sample_document.id,
                "strategy": "semantic_sentence",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] > 0
        assert all(
            c["metadata"]["chunking_strategy"] == "semantic_sentence"
            for c in data["chunks"]
        )

    @pytest.mark.asyncio
    async def test_chunk_document_sliding_window(self, client, sample_document):
        """Test chunking a document with sliding window strategy."""
        response = client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={
                "document_id": sample_document.id,
                "strategy": "sliding_window",
                "chunk_size": 256,
                "overlap": 50,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] > 0
        assert all(
            c["metadata"]["chunking_strategy"] == "sliding_window"
            for c in data["chunks"]
        )

    @pytest.mark.asyncio
    async def test_chunk_document_with_language_detection(self, client, sample_document):
        """Test chunking with language detection enabled."""
        response = client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={
                "document_id": sample_document.id,
                "strategy": "fixed_size",
                "detect_language": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] > 0
        # Language should be detected
        assert all(
            c["metadata"]["language"] is not None for c in data["chunks"]
        )

    @pytest.mark.asyncio
    async def test_chunk_nonexistent_document(self, client):
        """Test chunking nonexistent document returns 404."""
        response = client.post(
            "/api/documents/nonexistent-doc/chunk",
            json={"document_id": "nonexistent-doc", "strategy": "fixed_size"},
        )

        assert response.status_code == 404

    def test_chunk_document_without_text(self, client):
        """Test chunking document without extracted text."""
        # Create document without text
        doc = asyncio.run(create_document(
            filename="test.txt",
            file_content=b"Test",
            file_type="txt",
            file_size=4,
        ))
        # Don't extract text (set to empty)
        doc.text = None

        response = client.post(
            f"/api/documents/{doc.id}/chunk",
            json={"document_id": doc.id, "strategy": "fixed_size"},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_chunk_quality_scores_populated(self, client, sample_document):
        """Test that chunk quality scores are populated."""
        response = client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )

        assert response.status_code == 200
        data = response.json()
        for chunk in data["chunks"]:
            assert "quality_score" in chunk["metadata"]
            assert 0.0 <= chunk["metadata"]["quality_score"] <= 1.0
            assert "quality_level" in chunk["metadata"]


class TestSearchChunksEndpoint:
    """Tests for POST /api/chunks/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_chunks_no_filters(self, client, sample_document):
        """Test chunk search without filters."""
        # Create chunks
        client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )

        response = client.post("/api/chunks/search", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] > 0
        assert "query_time_ms" in data

    @pytest.mark.asyncio
    async def test_search_chunks_by_text(self, client, sample_document):
        """Test searching chunks by text content."""
        # Create chunks
        client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )

        response = client.post(
            "/api/chunks/search", json={"query": "introduction"}
        )

        assert response.status_code == 200
        data = response.json()
        # May or may not find results depending on chunking
        assert "results" in data
        assert "total_count" in data

    @pytest.mark.asyncio
    async def test_search_chunks_by_document(self, client, sample_document):
        """Test searching chunks filtered by document."""
        # Create chunks
        client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )

        response = client.post(
            "/api/chunks/search",
            json={"document_id": sample_document.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert all(c["document_id"] == sample_document.id for c in data["results"])

    @pytest.mark.asyncio
    async def test_search_chunks_by_quality(self, client, sample_document):
        """Test searching chunks by minimum quality score."""
        # Create chunks
        client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )

        response = client.post(
            "/api/chunks/search",
            json={"min_quality_score": 0.5},
        )

        assert response.status_code == 200
        data = response.json()
        for chunk in data["results"]:
            assert chunk["metadata"]["quality_score"] >= 0.5

    @pytest.mark.asyncio
    async def test_search_chunks_pagination(self, client, sample_document):
        """Test pagination in chunk search."""
        # Create chunks
        client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )

        response = client.post(
            "/api/chunks/search",
            json={"limit": 2, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 2


class TestChunkStatsEndpoints:
    """Tests for chunk statistics endpoints."""

    @pytest.mark.asyncio
    async def test_get_document_chunk_stats(self, client, sample_document):
        """Test getting chunk statistics for a document."""
        # Create chunks
        client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )

        response = client.get(f"/api/chunks/document/{sample_document.id}/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_chunks" in data
        assert "avg_chunk_size" in data
        assert "avg_quality_score" in data
        assert "quality_distribution" in data

    @pytest.mark.asyncio
    async def test_get_overall_chunk_stats(self, client, sample_document):
        """Test getting overall chunk statistics."""
        # Create chunks
        client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )

        response = client.get("/api/chunks/stats/summary")

        assert response.status_code == 200
        data = response.json()
        assert "total_chunks" in data
        assert "avg_chunk_size" in data
        assert "quality_distribution" in data

    @pytest.mark.asyncio
    async def test_chunk_stats_for_nonexistent_document(self, client):
        """Test chunk stats for nonexistent document."""
        response = client.get("/api/chunks/document/nonexistent/stats")

        assert response.status_code == 404


class TestChunkEndpointErrors:
    """Tests for error handling in chunk endpoints."""

    @pytest.mark.asyncio
    async def test_invalid_chunk_id_format(self, client):
        """Test getting chunk with invalid ID format."""
        response = client.get("/api/chunks/invalid")

        # Should return 404 since chunk doesn't exist
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_document_id_format(self, client):
        """Test operations with invalid document ID format."""
        response = client.get("/api/chunks/document/invalid")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_chunking_with_invalid_strategy(self, client, sample_document):
        """Test chunking with invalid strategy."""
        response = client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={
                "document_id": sample_document.id,
                "strategy": "invalid_strategy",
            },
        )

        assert response.status_code == 500


class TestChunkMetadataRoundtrip:
    """Tests for chunk metadata preservation through endpoints."""

    @pytest.mark.asyncio
    async def test_metadata_preserved_in_response(self, client, sample_document):
        """Test that all metadata is preserved in API responses."""
        # Create chunks
        response = client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )

        assert response.status_code == 200
        chunks = response.json()["chunks"]

        for chunk in chunks:
            metadata = chunk["metadata"]
            assert "document_id" in metadata
            assert "start_position" in metadata
            assert "end_position" in metadata
            assert "sentence_count" in metadata
            assert "quality_score" in metadata
            assert "quality_level" in metadata
            assert "chunking_strategy" in metadata
            # Language should be present if detected
            assert "language" in metadata

    @pytest.mark.asyncio
    async def test_chunk_positions_valid(self, client, sample_document):
        """Test that chunk positions are valid."""
        response = client.post(
            f"/api/documents/{sample_document.id}/chunk",
            json={"document_id": sample_document.id, "strategy": "fixed_size"},
        )

        assert response.status_code == 200
        chunks = response.json()["chunks"]

        for chunk in chunks:
            start = chunk["metadata"]["start_position"]
            end = chunk["metadata"]["end_position"]
            assert start >= 0
            assert end > start
            # Text length should match approximately
            assert 0 <= len(chunk["text"]) <= end - start + 100
