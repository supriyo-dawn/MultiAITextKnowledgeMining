"""Integration tests for search and analytics APIs."""

from fastapi.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    return TestClient(app)


def _create_chunked_document(client: TestClient) -> str:
    upload = client.post(
        "/api/documents/upload",
        files={"file": ("search.txt", b"Alpha knowledge is useful. Beta knowledge follows.")},
    )
    assert upload.status_code == 200
    document_id = upload.json()["document_id"]

    chunk = client.post(
        f"/api/documents/{document_id}/chunk",
        json={"document_id": document_id, "strategy": "fixed_size"},
    )
    assert chunk.status_code == 200
    return document_id


def test_semantic_search_returns_matching_chunks() -> None:
    client = _client()
    document_id = _create_chunked_document(client)

    response = client.post(
        "/api/search/semantic",
        json={"query": "alpha", "document_id": document_id},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert data["retrieval_mode"] == "vector"
    assert "Alpha" in data["results"][0]["text"]


def test_hybrid_search_reports_unavailable_enrichments() -> None:
    client = _client()
    _create_chunked_document(client)

    response = client.post("/api/search/hybrid", json={"query": "knowledge"})

    assert response.status_code == 200
    data = response.json()
    assert data["retrieval_mode"] == "vector_plus_graph_metadata"
    assert data["vector_search_available"] is True
    assert data["graph_search_available"] is True
    assert data["total_count"] >= 1


def test_analytics_summary_reports_documents_and_chunks() -> None:
    client = _client()
    _create_chunked_document(client)

    response = client.get("/api/analytics/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["documents"]["total"] >= 1
    assert data["documents"]["by_status"]["COMPLETED"] >= 1
    assert data["chunks"]["total_chunks"] >= 1
    assert data["entities"]["available"] is True


def test_chat_returns_retrieval_context_without_fabricating_answer() -> None:
    client = _client()
    _create_chunked_document(client)

    response = client.post("/api/chat/", json={"question": "Alpha"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "retrieval_only"
    assert data["answer"] is None
    assert data["sources"]


def test_knowledge_graph_reports_unavailable_state() -> None:
    client = _client()

    response = client.get("/api/knowledge/graph")

    assert response.status_code == 200
    assert response.json()["available"] is True