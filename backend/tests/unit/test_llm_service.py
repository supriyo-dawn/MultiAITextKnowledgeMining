import pytest

from app.services.llm_service import generate_answer


@pytest.mark.asyncio
async def test_llm_fallback_without_api_key(monkeypatch):
    monkeypatch.setattr("app.services.llm_service.settings.OPENAI_API_KEY", "")
    assert await generate_answer("question", ["context"]) is None


@pytest.mark.asyncio
async def test_llm_fallback_without_sources(monkeypatch):
    monkeypatch.setattr("app.services.llm_service.settings.OPENAI_API_KEY", "key")
    assert await generate_answer("question", []) is None
