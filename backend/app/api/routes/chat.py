"""API routes for retrieval-assisted chat."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.routes.chunks import chunk_service
from app.services.llm_service import generate_answer

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Question submitted to the chat endpoint."""

    question: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


@router.post("/")
async def chat(request: ChatRequest):
    """Retrieve relevant passages until an LLM provider is configured."""
    results, total = await chunk_service.search_chunks(
        query=request.question,
        limit=request.limit,
    )
    answer = await generate_answer(request.question, [chunk.text for chunk in results])
    return {
        "status": "answered" if answer else "retrieval_only",
        "answer": answer,
        "message": "Answer generated from retrieved context." if answer else "Relevant passages retrieved; LLM answer generation is not configured.",
        "sources": [
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }
            for chunk in results
        ],
        "total_matches": total,
    }
