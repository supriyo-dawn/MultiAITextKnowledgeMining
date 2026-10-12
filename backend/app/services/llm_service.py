"""Optional LLM answer generation with a deterministic local fallback."""

from app.core.config import settings


async def generate_answer(question: str, sources: list[str]) -> str | None:
    if not settings.OPENAI_API_KEY or not sources:
        return None
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        context = "\n\n".join(sources)
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "Answer using only the supplied context. Cite the relevant context briefly."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            temperature=0,
        )
        return response.choices[0].message.content
    except Exception:
        return None
