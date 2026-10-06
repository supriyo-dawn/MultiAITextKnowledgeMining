"""
Chunk storage and retrieval service.

Phase A: Uses SQLite via SQLAlchemy for persistent storage.
Previously used in-memory dictionaries with manual indexes (Phase 3).
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import delete, func, select

from app.core.database import async_session_factory
from app.models.chunk import Chunk, ChunkMetadata, ChunkQualityLevel, ChunkingStrategy
from app.models.db_models import ChunkDB

logger = logging.getLogger(__name__)


class ChunkServiceError(Exception):
    """Exception raised by chunk service."""
    pass


# ── Conversion helpers ──────────────────────────────────────────

def _db_to_pydantic(db_chunk: ChunkDB) -> Chunk:
    """Convert a SQLAlchemy ChunkDB row to a Pydantic Chunk."""
    return Chunk(
        id=db_chunk.id,
        document_id=db_chunk.document_id,
        text=db_chunk.text,
        metadata=ChunkMetadata(
            document_id=db_chunk.document_id,
            start_position=db_chunk.start_position,
            end_position=db_chunk.end_position,
            section=db_chunk.section,
            paragraph_index=db_chunk.paragraph_index,
            sentence_count=db_chunk.sentence_count,
            quality_score=db_chunk.quality_score,
            quality_level=ChunkQualityLevel(db_chunk.quality_level),
            language=db_chunk.language,
            is_normalized=db_chunk.is_normalized,
            token_count=db_chunk.token_count,
            chunking_strategy=ChunkingStrategy(db_chunk.chunking_strategy),
        ),
        created_at=db_chunk.created_at,
        updated_at=db_chunk.updated_at,
    )


def _quality_level_from_score(score: float) -> str:
    """Determine quality level string from numeric score."""
    if score >= 0.75:
        return ChunkQualityLevel.HIGH.value
    elif score >= 0.5:
        return ChunkQualityLevel.MEDIUM.value
    return ChunkQualityLevel.LOW.value


# ── Service class ───────────────────────────────────────────────

class ChunkService:
    """
    Chunk storage and retrieval service backed by SQLite.

    Provides CRUD, search, and statistics for document chunks.
    """

    def __init__(self):
        self.logger = logger

    async def create_chunk(
        self,
        document_id: str,
        text: str,
        start_position: int,
        end_position: int,
        sentence_count: int = 1,
        section: Optional[str] = None,
        paragraph_index: Optional[int] = None,
        quality_score: float = 0.0,
        language: Optional[str] = None,
        is_normalized: bool = False,
        token_count: Optional[int] = None,
        chunking_strategy: str = "fixed_size",
    ) -> Chunk:
        """Create and store a new chunk."""
        if not text or not isinstance(text, str):
            raise ChunkServiceError("Chunk text must be non-empty string")
        if not document_id:
            raise ChunkServiceError("document_id is required")
        if start_position < 0 or end_position < 0:
            raise ChunkServiceError("Positions must be non-negative")
        if end_position <= start_position:
            raise ChunkServiceError("end_position must be greater than start_position")

        try:
            quality_level = _quality_level_from_score(quality_score)

            async with async_session_factory() as session:
                db_chunk = ChunkDB(
                    id=str(uuid4()),
                    document_id=document_id,
                    text=text,
                    start_position=start_position,
                    end_position=end_position,
                    section=section,
                    paragraph_index=paragraph_index,
                    sentence_count=sentence_count,
                    quality_score=quality_score,
                    quality_level=quality_level,
                    language=language,
                    is_normalized=is_normalized,
                    token_count=token_count,
                    chunking_strategy=chunking_strategy,
                )
                session.add(db_chunk)
                await session.commit()
                await session.refresh(db_chunk)

                self.logger.info(
                    f"Created chunk {db_chunk.id} for document {document_id} "
                    f"(text_len={len(text)}, quality={quality_score:.2f})"
                )

                return _db_to_pydantic(db_chunk)

        except ChunkServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create chunk: {str(e)}")
            raise ChunkServiceError(f"Failed to create chunk: {str(e)}") from e

    async def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Retrieve a chunk by ID."""
        async with async_session_factory() as session:
            result = await session.execute(
                select(ChunkDB).where(ChunkDB.id == chunk_id)
            )
            db_chunk = result.scalar_one_or_none()
            return _db_to_pydantic(db_chunk) if db_chunk else None

    async def get_chunks_by_document(
        self, document_id: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[Chunk], int]:
        """Retrieve all chunks for a document with pagination."""
        async with async_session_factory() as session:
            # Count
            count_result = await session.execute(
                select(func.count(ChunkDB.id)).where(
                    ChunkDB.document_id == document_id
                )
            )
            total = count_result.scalar() or 0

            # Paginated results
            result = await session.execute(
                select(ChunkDB)
                .where(ChunkDB.document_id == document_id)
                .order_by(ChunkDB.start_position)
                .limit(limit)
                .offset(offset)
            )
            db_chunks = result.scalars().all()

            return [_db_to_pydantic(c) for c in db_chunks], total

    async def get_chunks_by_section(
        self, section: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[Chunk], int]:
        """Retrieve all chunks from a document section."""
        async with async_session_factory() as session:
            count_result = await session.execute(
                select(func.count(ChunkDB.id)).where(ChunkDB.section == section)
            )
            total = count_result.scalar() or 0

            result = await session.execute(
                select(ChunkDB)
                .where(ChunkDB.section == section)
                .limit(limit)
                .offset(offset)
            )
            db_chunks = result.scalars().all()

            return [_db_to_pydantic(c) for c in db_chunks], total

    async def list_chunks(
        self, limit: int = 100, offset: int = 0
    ) -> tuple[list[Chunk], int]:
        """List all chunks with pagination."""
        async with async_session_factory() as session:
            count_result = await session.execute(select(func.count(ChunkDB.id)))
            total = count_result.scalar() or 0

            result = await session.execute(
                select(ChunkDB)
                .order_by(ChunkDB.created_at)
                .limit(limit)
                .offset(offset)
            )
            db_chunks = result.scalars().all()

            return [_db_to_pydantic(c) for c in db_chunks], total

    async def search_chunks(
        self,
        query: Optional[str] = None,
        document_id: Optional[str] = None,
        min_quality_score: Optional[float] = None,
        section: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[Chunk], int]:
        """Search chunks with multiple filters."""
        async with async_session_factory() as session:
            # Build query dynamically
            stmt = select(ChunkDB)
            count_stmt = select(func.count(ChunkDB.id))

            if query:
                # SQLite LIKE for substring search
                filter_expr = ChunkDB.text.ilike(f"%{query}%")
                stmt = stmt.where(filter_expr)
                count_stmt = count_stmt.where(filter_expr)

            if document_id:
                stmt = stmt.where(ChunkDB.document_id == document_id)
                count_stmt = count_stmt.where(ChunkDB.document_id == document_id)

            if min_quality_score is not None:
                stmt = stmt.where(ChunkDB.quality_score >= min_quality_score)
                count_stmt = count_stmt.where(ChunkDB.quality_score >= min_quality_score)

            if section:
                stmt = stmt.where(ChunkDB.section == section)
                count_stmt = count_stmt.where(ChunkDB.section == section)

            if language:
                stmt = stmt.where(ChunkDB.language == language)
                count_stmt = count_stmt.where(ChunkDB.language == language)

            # Get count
            count_result = await session.execute(count_stmt)
            total = count_result.scalar() or 0

            # Get results sorted by quality desc, then creation time desc
            result = await session.execute(
                stmt.order_by(
                    ChunkDB.quality_score.desc(),
                    ChunkDB.created_at.desc(),
                )
                .limit(limit)
                .offset(offset)
            )
            db_chunks = result.scalars().all()

            self.logger.info(
                f"Chunk search: {len(db_chunks)} results (total: {total}) "
                f"with filters: query={query}, doc_id={document_id}, "
                f"min_quality={min_quality_score}"
            )

            return [_db_to_pydantic(c) for c in db_chunks], total

    async def update_chunk(
        self,
        chunk_id: str,
        text: Optional[str] = None,
        quality_score: Optional[float] = None,
        section: Optional[str] = None,
        **kwargs,
    ) -> Optional[Chunk]:
        """Update a chunk."""
        async with async_session_factory() as session:
            result = await session.execute(
                select(ChunkDB).where(ChunkDB.id == chunk_id)
            )
            db_chunk = result.scalar_one_or_none()

            if not db_chunk:
                self.logger.warning(f"Chunk not found: {chunk_id}")
                return None

            if text is not None:
                db_chunk.text = text
            if quality_score is not None:
                db_chunk.quality_score = quality_score
                db_chunk.quality_level = _quality_level_from_score(quality_score)
            if section is not None:
                db_chunk.section = section

            db_chunk.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(db_chunk)

            self.logger.info(f"Updated chunk {chunk_id}")
            return _db_to_pydantic(db_chunk)

    async def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk."""
        async with async_session_factory() as session:
            result = await session.execute(
                select(ChunkDB).where(ChunkDB.id == chunk_id)
            )
            db_chunk = result.scalar_one_or_none()

            if not db_chunk:
                self.logger.warning(f"Chunk not found: {chunk_id}")
                return False

            await session.delete(db_chunk)
            await session.commit()
            self.logger.info(f"Deleted chunk {chunk_id}")
            return True

    async def delete_document_chunks(self, document_id: str) -> int:
        """Delete all chunks for a document."""
        async with async_session_factory() as session:
            # Count first
            count_result = await session.execute(
                select(func.count(ChunkDB.id)).where(
                    ChunkDB.document_id == document_id
                )
            )
            count = count_result.scalar() or 0

            if count > 0:
                await session.execute(
                    delete(ChunkDB).where(ChunkDB.document_id == document_id)
                )
                await session.commit()
                self.logger.info(
                    f"Deleted {count} chunks for document {document_id}"
                )

            return count

    async def get_chunk_count(self, document_id: Optional[str] = None) -> int:
        """Get total chunk count."""
        async with async_session_factory() as session:
            stmt = select(func.count(ChunkDB.id))
            if document_id:
                stmt = stmt.where(ChunkDB.document_id == document_id)
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def get_statistics(self, document_id: Optional[str] = None) -> dict:
        """Get chunk statistics."""
        if document_id:
            chunks, total = await self.get_chunks_by_document(
                document_id, limit=10000
            )
        else:
            chunks, total = await self.list_chunks(limit=10000)

        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_size": 0,
                "avg_quality_score": 0.0,
                "quality_distribution": {},
                "language_distribution": {},
                "strategy_distribution": {},
            }

        chunk_sizes = [len(c.text) for c in chunks]
        quality_scores = [c.metadata.quality_score for c in chunks]
        languages = {}
        strategies = {}
        quality_dist = {"high": 0, "medium": 0, "low": 0}

        for chunk in chunks:
            lang = chunk.metadata.language or "unknown"
            languages[lang] = languages.get(lang, 0) + 1

            strat = chunk.metadata.chunking_strategy.value
            strategies[strat] = strategies.get(strat, 0) + 1

            level = chunk.metadata.quality_level.value
            quality_dist[level] = quality_dist.get(level, 0) + 1

        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
            "min_chunk_size": min(chunk_sizes) if chunk_sizes else 0,
            "max_chunk_size": max(chunk_sizes) if chunk_sizes else 0,
            "avg_quality_score": sum(quality_scores) / len(quality_scores)
            if quality_scores else 0,
            "quality_distribution": quality_dist,
            "language_distribution": languages,
            "strategy_distribution": strategies,
        }
