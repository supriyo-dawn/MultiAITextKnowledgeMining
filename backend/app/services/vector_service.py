"""Deterministic local vector indexing with optional FAISS acceleration."""

import hashlib
import json
import math

import numpy as np
from sqlalchemy import delete, select

from app.core.database import async_session_factory
from app.models.chunk import Chunk
from app.models.db_models import ChunkDB, EmbeddingDB

_DIMENSIONS = 128
_chunks: dict[str, Chunk] = {}
_vectors: dict[str, np.ndarray] = {}


def embed_text(text: str) -> np.ndarray:
    vector = np.zeros(_DIMENSIONS, dtype=np.float32)
    tokens = text.lower().split()
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % _DIMENSIONS
        vector[index] += 1.0
    norm = math.sqrt(float(np.dot(vector, vector)))
    return vector / norm if norm else vector


def index_chunks(chunks: list[Chunk]) -> None:
    for chunk in chunks:
        _chunks[chunk.id] = chunk
        _vectors[chunk.id] = embed_text(chunk.text)


async def persist_chunk_embeddings(chunks: list[Chunk]) -> None:
    """Upsert deterministic embeddings in the existing SQL database."""

    async with async_session_factory() as session:
        for chunk in chunks:
            vector = embed_text(chunk.text)
            row = await session.get(EmbeddingDB, chunk.id)
            if row:
                row.vector_json = json.dumps(vector.tolist(), separators=(",", ":"))
                row.dimensions = _DIMENSIONS
            else:
                session.add(EmbeddingDB(
                    chunk_id=chunk.id,
                    dimensions=_DIMENSIONS,
                    vector_json=json.dumps(vector.tolist(), separators=(",", ":")),
                ))
        await session.commit()
        index_chunks(chunks)


async def persistent_search(
    query: str, limit: int = 10, document_id: str | None = None
) -> tuple[list[Chunk], int]:
    """Search durable embeddings, rebuilding no in-memory index."""

    query_vector = embed_text(query)
    async with async_session_factory() as session:
        query_stmt = select(EmbeddingDB, ChunkDB).join(
            ChunkDB, ChunkDB.id == EmbeddingDB.chunk_id
        )
        if document_id:
            query_stmt = query_stmt.where(ChunkDB.document_id == document_id)
        rows = (await session.execute(query_stmt)).all()
    ranked: list[tuple[float, Chunk]] = []
    from app.services.chunk_service import _db_to_pydantic
    for embedding, db_chunk in rows:
        vector = np.asarray(json.loads(embedding.vector_json), dtype=np.float32)
        ranked.append((float(np.dot(query_vector, vector)), _db_to_pydantic(db_chunk)))
    ranked.sort(key=lambda item: (-item[0], item[1].id))
    matches = [chunk for score, chunk in ranked if score > 0]
    return matches[:limit], len(matches)


def remove_document(document_id: str) -> None:
    for chunk_id in [key for key, value in _chunks.items() if value.document_id == document_id]:
        _chunks.pop(chunk_id, None)
        _vectors.pop(chunk_id, None)


def search(query: str, limit: int = 10, document_id: str | None = None) -> tuple[list[Chunk], int]:
    query_vector = embed_text(query)
    ranked = []
    for chunk_id, vector in _vectors.items():
        chunk = _chunks[chunk_id]
        if document_id and chunk.document_id != document_id:
            continue
        ranked.append((float(np.dot(query_vector, vector)), chunk))
    ranked.sort(key=lambda item: item[0], reverse=True)
    matches = [chunk for score, chunk in ranked if score > 0]
    return matches[:limit], len(matches)
