from app.services.vector_service import embed_text, search, index_chunks
from app.models.chunk import Chunk, ChunkMetadata, ChunkingStrategy


def _chunk(text: str) -> Chunk:
    return Chunk(document_id="doc", text=text, metadata=ChunkMetadata(document_id="doc", start_position=0, end_position=len(text), chunking_strategy=ChunkingStrategy.FIXED_SIZE))


def test_embed_text_is_normalized_and_deterministic():
    first = embed_text("Alpha beta")
    second = embed_text("Alpha beta")
    assert first.shape == second.shape
    assert (first == second).all()
    assert abs(float((first * first).sum()) - 1.0) < 0.001


def test_vector_search_ranks_matching_chunk():
    chunks = [_chunk("alpha project"), _chunk("unrelated words")]
    index_chunks(chunks)
    results, total = search("alpha")
    assert total >= 1
    assert results[0].text == "alpha project"
