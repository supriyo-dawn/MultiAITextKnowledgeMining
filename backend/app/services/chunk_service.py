"""
Chunk storage and retrieval service.

Provides in-memory chunk storage and search functionality.
In Phase 6, this will be replaced with database storage.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.models.chunk import Chunk, ChunkMetadata, ChunkQualityLevel, ChunkingStrategy

logger = logging.getLogger(__name__)


class ChunkServiceError(Exception):
    """Exception raised by chunk service."""

    pass


class ChunkService:
    """
    In-memory chunk storage and retrieval service.

    Stores chunks from documents and provides search/retrieval capabilities.
    Storage is in-memory only (Phase 3 MVP).
    """

    def __init__(self):
        """Initialize the chunk service."""
        # In-memory storage: chunk_id -> Chunk
        self._chunks: dict[str, Chunk] = {}
        # Index: document_id -> list of chunk_ids
        self._document_index: dict[str, list[str]] = {}
        # Index: section -> list of chunk_ids
        self._section_index: dict[str, list[str]] = {}
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
        """
        Create and store a new chunk.

        Args:
            document_id: Parent document ID
            text: Chunk text content
            start_position: Character offset in original document
            end_position: Character offset in original document
            sentence_count: Number of sentences in chunk
            section: Optional document section
            paragraph_index: Paragraph number
            quality_score: Quality score (0-1)
            language: Detected language code
            is_normalized: Whether text was normalized
            token_count: Estimated token count
            chunking_strategy: Chunking strategy used

        Returns:
            Created Chunk object

        Raises:
            ChunkServiceError: If chunk creation fails
        """
        try:
            if not text or not isinstance(text, str):
                raise ChunkServiceError("Chunk text must be non-empty string")

            if not document_id:
                raise ChunkServiceError("document_id is required")

            if start_position < 0 or end_position < 0:
                raise ChunkServiceError("Positions must be non-negative")

            if end_position <= start_position:
                raise ChunkServiceError("end_position must be greater than start_position")

            # Determine quality level based on score
            if quality_score >= 0.75:
                quality_level = ChunkQualityLevel.HIGH
            elif quality_score >= 0.5:
                quality_level = ChunkQualityLevel.MEDIUM
            else:
                quality_level = ChunkQualityLevel.LOW

            # Create metadata
            metadata = ChunkMetadata(
                document_id=document_id,
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
                chunking_strategy=ChunkingStrategy(chunking_strategy),
            )

            # Create chunk
            chunk = Chunk(
                id=str(uuid4()),
                document_id=document_id,
                text=text,
                metadata=metadata,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            # Store in memory
            self._chunks[chunk.id] = chunk

            # Update indexes
            if document_id not in self._document_index:
                self._document_index[document_id] = []
            self._document_index[document_id].append(chunk.id)

            if section:
                if section not in self._section_index:
                    self._section_index[section] = []
                self._section_index[section].append(chunk.id)

            self.logger.info(
                f"Created chunk {chunk.id} for document {document_id} "
                f"(text_len={len(text)}, quality={quality_score:.2f})"
            )

            return chunk

        except ChunkServiceError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create chunk: {str(e)}")
            raise ChunkServiceError(f"Failed to create chunk: {str(e)}") from e

    async def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """
        Retrieve a chunk by ID.

        Args:
            chunk_id: Chunk ID to retrieve

        Returns:
            Chunk object or None if not found
        """
        return self._chunks.get(chunk_id)

    async def get_chunks_by_document(
        self, document_id: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[Chunk], int]:
        """
        Retrieve all chunks for a document.

        Args:
            document_id: Document ID
            limit: Maximum results (default: 100)
            offset: Result offset (default: 0)

        Returns:
            Tuple of (chunk list, total count)
        """
        if document_id not in self._document_index:
            return [], 0

        chunk_ids = self._document_index[document_id]
        total_count = len(chunk_ids)

        # Apply pagination
        paginated_ids = chunk_ids[offset : offset + limit]
        chunks = [self._chunks[cid] for cid in paginated_ids if cid in self._chunks]

        return chunks, total_count

    async def get_chunks_by_section(
        self, section: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[Chunk], int]:
        """
        Retrieve all chunks from a document section.

        Args:
            section: Section name
            limit: Maximum results
            offset: Result offset

        Returns:
            Tuple of (chunk list, total count)
        """
        if section not in self._section_index:
            return [], 0

        chunk_ids = self._section_index[section]
        total_count = len(chunk_ids)

        # Apply pagination
        paginated_ids = chunk_ids[offset : offset + limit]
        chunks = [self._chunks[cid] for cid in paginated_ids if cid in self._chunks]

        return chunks, total_count

    async def list_chunks(
        self, limit: int = 100, offset: int = 0
    ) -> tuple[list[Chunk], int]:
        """
        List all chunks.

        Args:
            limit: Maximum results
            offset: Result offset

        Returns:
            Tuple of (chunk list, total count)
        """
        chunk_ids = list(self._chunks.keys())
        total_count = len(chunk_ids)

        # Apply pagination
        paginated_ids = chunk_ids[offset : offset + limit]
        chunks = [self._chunks[cid] for cid in paginated_ids]

        return chunks, total_count

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
        """
        Search chunks with multiple filters.

        Args:
            query: Text search query (simple substring match)
            document_id: Filter by document
            min_quality_score: Minimum quality score filter
            section: Filter by section
            language: Filter by language
            limit: Maximum results
            offset: Result offset

        Returns:
            Tuple of (matching chunks, total count)
        """
        # Start with all chunks
        candidates = list(self._chunks.values())

        # Apply filters
        if query:
            query_lower = query.lower()
            candidates = [c for c in candidates if query_lower in c.text.lower()]

        if document_id:
            candidates = [c for c in candidates if c.document_id == document_id]

        if min_quality_score is not None:
            candidates = [
                c for c in candidates
                if c.metadata.quality_score >= min_quality_score
            ]

        if section:
            candidates = [c for c in candidates if c.metadata.section == section]

        if language:
            candidates = [c for c in candidates if c.metadata.language == language]

        # Sort by quality score descending, then by creation time
        candidates.sort(
            key=lambda c: (c.metadata.quality_score, c.created_at), reverse=True
        )

        total_count = len(candidates)

        # Apply pagination
        results = candidates[offset : offset + limit]

        self.logger.info(
            f"Chunk search: {len(results)} results (total: {total_count}) "
            f"with filters: query={query}, doc_id={document_id}, "
            f"min_quality={min_quality_score}"
        )

        return results, total_count

    async def update_chunk(
        self,
        chunk_id: str,
        text: Optional[str] = None,
        quality_score: Optional[float] = None,
        section: Optional[str] = None,
        **kwargs,
    ) -> Optional[Chunk]:
        """
        Update a chunk.

        Args:
            chunk_id: Chunk ID to update
            text: New text (optional)
            quality_score: New quality score (optional)
            section: New section (optional)
            **kwargs: Additional fields to update

        Returns:
            Updated Chunk or None if not found
        """
        chunk = self._chunks.get(chunk_id)
        if not chunk:
            self.logger.warning(f"Chunk not found: {chunk_id}")
            return None

        # Update text if provided
        if text is not None:
            chunk.text = text

        # Update quality score if provided
        if quality_score is not None:
            chunk.metadata.quality_score = quality_score
            # Update quality level
            if quality_score >= 0.75:
                chunk.metadata.quality_level = ChunkQualityLevel.HIGH
            elif quality_score >= 0.5:
                chunk.metadata.quality_level = ChunkQualityLevel.MEDIUM
            else:
                chunk.metadata.quality_level = ChunkQualityLevel.LOW

        # Update section if provided
        if section is not None:
            old_section = chunk.metadata.section
            chunk.metadata.section = section

            # Update section index
            if old_section and old_section in self._section_index:
                if chunk_id in self._section_index[old_section]:
                    self._section_index[old_section].remove(chunk_id)

            if section not in self._section_index:
                self._section_index[section] = []
            self._section_index[section].append(chunk_id)

        # Update timestamp
        chunk.updated_at = datetime.utcnow()

        self.logger.info(f"Updated chunk {chunk_id}")

        return chunk

    async def delete_chunk(self, chunk_id: str) -> bool:
        """
        Delete a chunk.

        Args:
            chunk_id: Chunk ID to delete

        Returns:
            True if deleted, False if not found
        """
        chunk = self._chunks.get(chunk_id)
        if not chunk:
            self.logger.warning(f"Chunk not found: {chunk_id}")
            return False

        # Remove from indexes
        doc_id = chunk.document_id
        if doc_id in self._document_index:
            if chunk_id in self._document_index[doc_id]:
                self._document_index[doc_id].remove(chunk_id)

        section = chunk.metadata.section
        if section and section in self._section_index:
            if chunk_id in self._section_index[section]:
                self._section_index[section].remove(chunk_id)

        # Remove from storage
        del self._chunks[chunk_id]

        self.logger.info(f"Deleted chunk {chunk_id}")

        return True

    async def delete_document_chunks(self, document_id: str) -> int:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID

        Returns:
            Number of chunks deleted
        """
        if document_id not in self._document_index:
            return 0

        chunk_ids = self._document_index[document_id].copy()

        for chunk_id in chunk_ids:
            await self.delete_chunk(chunk_id)

        self.logger.info(f"Deleted {len(chunk_ids)} chunks for document {document_id}")

        return len(chunk_ids)

    async def get_chunk_count(self, document_id: Optional[str] = None) -> int:
        """
        Get total chunk count.

        Args:
            document_id: Optional filter by document

        Returns:
            Chunk count
        """
        if document_id:
            return len(self._document_index.get(document_id, []))
        return len(self._chunks)

    async def get_statistics(self, document_id: Optional[str] = None) -> dict:
        """
        Get chunk statistics.

        Args:
            document_id: Optional filter by document

        Returns:
            Dictionary with statistics
        """
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
            # Count languages
            lang = chunk.metadata.language or "unknown"
            languages[lang] = languages.get(lang, 0) + 1

            # Count strategies
            strat = chunk.metadata.chunking_strategy.value
            strategies[strat] = strategies.get(strat, 0) + 1

            # Count quality levels
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
