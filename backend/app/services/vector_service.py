"""Deterministic local vector indexing with optional FAISS acceleration."""

import hashlib
import math

import numpy as np

from app.models.chunk import Chunk

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
