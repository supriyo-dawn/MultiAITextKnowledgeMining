import pytest

from app.models.chunk import ChunkMetadata
from app.services.chunk_service import ChunkService
from app.services.vector_service import persistent_search


@pytest.mark.asyncio
async def test_chunk_embedding_survives_vector_service_memory_reset():
    service = ChunkService()
    chunk = await service.create_chunk(
        document_id="doc-vector",
        text="Deterministic vector indexing supports retrieval.",
        start_position=0,
        end_position=50,
    )

    # The query reads the SQL-backed embedding, not the process-local index.
    from app.services import vector_service
    vector_service._chunks.clear()
    vector_service._vectors.clear()

    results, total = await persistent_search("deterministic retrieval", limit=5)

    assert total == 1
    assert results[0].id == chunk.id
    assert results[0].document_id == "doc-vector"
