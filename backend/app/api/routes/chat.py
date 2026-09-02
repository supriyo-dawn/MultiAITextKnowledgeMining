"""API routes for RAG chatbot."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/")
async def chat():
    """Answer user questions via RAG with source citations. (Phase 1 stub)"""
    return {"message": "RAG chatbot coming in Phase 10"}
