"""API routes for retrieval-assisted chat."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.routes.chunks import chunk_service
from app.services.llm_service import generate_answer
from app.services.vector_service import persistent_search

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Question submitted to the chat endpoint."""

    question: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


@router.post("/")
async def chat(request: ChatRequest):
    """Retrieve relevant passages until an LLM provider is configured."""
    results, total = await persistent_search(request.question, request.limit)
    if not results:
        results, total = await chunk_service.search_chunks(
            query=request.question,
            limit=request.limit,
        )
    labelled_sources = [f"[S{index}] {chunk.text}" for index, chunk in enumerate(results, 1)]
    answer = await generate_answer(request.question, labelled_sources)
    return {
        "status": "answered" if answer else "retrieval_only",
        "answer": answer,
        "message": "Answer generated from retrieved context." if answer else "Relevant passages retrieved; LLM answer generation is not configured.",
        "sources": [
            {
                "citation": f"S{index}",
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }
            for index, chunk in enumerate(results, 1)
        ],
        "citations": [f"S{index}" for index, _ in enumerate(results, 1)],
        "total_matches": total,
    }
