"""
Unit tests for chunk storage and retrieval service.

Tests:
- Chunk creation and storage
- Chunk retrieval (single, by document, search)
- Chunk updates and deletion
- In-memory indexing
- Statistics and aggregations
"""

import pytest

from app.models.chunk import ChunkQualityLevel, ChunkingStrategy
from app.services.chunk_service import ChunkService, ChunkServiceError


@pytest.fixture
def chunk_service():
    """Create a chunk service instance."""
    return ChunkService()


class TestChunkCreation:
    """Tests for chunk creation and storage."""

    @pytest.mark.asyncio
    async def test_create_chunk_basic(self, chunk_service):
        """Test basic chunk creation."""
        chunk = await chunk_service.create_chunk(
            document_id="doc1",
            text="Sample chunk text",
            start_position=0,
            end_position=17,
        )

        assert chunk.id is not None
        assert chunk.document_id == "doc1"
        assert chunk.text == "Sample chunk text"
        assert chunk.metadata.start_position == 0
        assert chunk.metadata.end_position == 17

    @pytest.mark.asyncio
    async def test_create_chunk_with_metadata(self, chunk_service):
        """Test chunk creation with full metadata."""
        chunk = await chunk_service.create_chunk(
            document_id="doc1",
            text="Sample text",
            start_position=0,
            end_position=11,
            section="Introduction",
            paragraph_index=1,
            sentence_count=2,
            quality_score=0.85,
            language="en",
            token_count=5,
        )

        assert chunk.metadata.section == "Introduction"
        assert chunk.metadata.paragraph_index == 1
        assert chunk.metadata.sentence_count == 2
        assert chunk.metadata.quality_score == 0.85
        assert chunk.metadata.language == "en"
        assert chunk.metadata.token_count == 5

    @pytest.mark.asyncio
    async def test_quality_level_assignment_high(self, chunk_service):
        """Test that high quality score assigns HIGH level."""
        chunk = await chunk_service.create_chunk(
            document_id="doc1",
            text="Text",
            start_position=0,
            end_position=4,
            quality_score=0.85,
        )

        assert chunk.metadata.quality_level == ChunkQualityLevel.HIGH

    @pytest.mark.asyncio
    async def test_quality_level_assignment_medium(self, chunk_service):
        """Test that medium quality score assigns MEDIUM level."""
        chunk = await chunk_service.create_chunk(
            document_id="doc1",
            text="Text",
            start_position=0,
            end_position=4,
            quality_score=0.65,
        )

        assert chunk.metadata.quality_level == ChunkQualityLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_quality_level_assignment_low(self, chunk_service):
        """Test that low quality score assigns LOW level."""
        chunk = await chunk_service.create_chunk(
            document_id="doc1",
            text="Text",
            start_position=0,
            end_position=4,
            quality_score=0.30,
        )

        assert chunk.metadata.quality_level == ChunkQualityLevel.LOW

    @pytest.mark.asyncio
    async def test_empty_text_raises_error(self, chunk_service):
        """Test that empty text raises error."""
        with pytest.raises(ChunkServiceError):
            await chunk_service.create_chunk(
                document_id="doc1", text="", start_position=0, end_position=0
            )

    @pytest.mark.asyncio
    async def test_empty_document_id_raises_error(self, chunk_service):
        """Test that empty document_id raises error."""
        with pytest.raises(ChunkServiceError):
            await chunk_service.create_chunk(
                document_id="",
                text="Text",
                start_position=0,
                end_position=4,
            )

    @pytest.mark.asyncio
    async def test_invalid_positions_raise_error(self, chunk_service):
        """Test that invalid positions raise error."""
        with pytest.raises(ChunkServiceError):
            await chunk_service.create_chunk(
                document_id="doc1",
                text="Text",
                start_position=10,
                end_position=5,  # End < start
            )

    @pytest.mark.asyncio
    async def test_negative_positions_raise_error(self, chunk_service):
        """Test that negative positions raise error."""
        with pytest.raises(ChunkServiceError):
            await chunk_service.create_chunk(
                document_id="doc1",
                text="Text",
                start_position=-1,
                end_position=4,
            )


class TestChunkRetrieval:
    """Tests for chunk retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_chunk_by_id(self, chunk_service):
        """Test retrieving a chunk by ID."""
        created = await chunk_service.create_chunk(
            document_id="doc1",
            text="Sample text",
            start_position=0,
            end_position=11,
        )

        retrieved = await chunk_service.get_chunk(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.text == "Sample text"

    @pytest.mark.asyncio
    async def test_get_nonexistent_chunk_returns_none(self, chunk_service):
        """Test that getting nonexistent chunk returns None."""
        chunk = await chunk_service.get_chunk("nonexistent")
        assert chunk is None

    @pytest.mark.asyncio
    async def test_get_chunks_by_document(self, chunk_service):
        """Test retrieving all chunks for a document."""
        # Create multiple chunks
        for i in range(5):
            await chunk_service.create_chunk(
                document_id="doc1",
                text=f"Chunk {i}",
                start_position=i * 10,
                end_position=(i + 1) * 10,
            )

        chunks, total = await chunk_service.get_chunks_by_document("doc1")

        assert len(chunks) == 5
        assert total == 5

    @pytest.mark.asyncio
    async def test_get_chunks_by_nonexistent_document(self, chunk_service):
        """Test retrieving chunks for nonexistent document."""
        chunks, total = await chunk_service.get_chunks_by_document("nonexistent")

        assert len(chunks) == 0
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_chunks_by_section(self, chunk_service):
        """Test retrieving chunks by section."""
        # Create chunks with different sections
        await chunk_service.create_chunk(
            document_id="doc1",
            text="Intro text",
            start_position=0,
            end_position=10,
            section="Introduction",
        )
        await chunk_service.create_chunk(
            document_id="doc1",
            text="Body text",
            start_position=10,
            end_position=19,
            section="Body",
        )

        intro_chunks, intro_total = await chunk_service.get_chunks_by_section(
            "Introduction"
        )

        assert len(intro_chunks) == 1
        assert intro_total == 1
        assert intro_chunks[0].text == "Intro text"

    @pytest.mark.asyncio
    async def test_pagination(self, chunk_service):
        """Test pagination in chunk retrieval."""
        # Create 25 chunks
        for i in range(25):
            await chunk_service.create_chunk(
                document_id="doc1",
                text=f"Chunk {i}",
                start_position=i * 10,
                end_position=(i + 1) * 10,
            )

        # Get first page (10 items)
        page1, total1 = await chunk_service.get_chunks_by_document(
            "doc1", limit=10, offset=0
        )
        assert len(page1) == 10
        assert total1 == 25

        # Get second page
        page2, total2 = await chunk_service.get_chunks_by_document(
            "doc1", limit=10, offset=10
        )
        assert len(page2) == 10
        assert total2 == 25

        # Verify different chunks
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_list_all_chunks(self, chunk_service):
        """Test listing all chunks."""
        # Create chunks for multiple documents
        for doc_idx in range(2):
            for chunk_idx in range(3):
                await chunk_service.create_chunk(
                    document_id=f"doc{doc_idx}",
                    text=f"Chunk {chunk_idx}",
                    start_position=chunk_idx * 10,
                    end_position=(chunk_idx + 1) * 10,
                )

        chunks, total = await chunk_service.list_chunks()

        assert len(chunks) == 6
        assert total == 6


class TestChunkUpdates:
    """Tests for chunk update operations."""

    @pytest.mark.asyncio
    async def test_update_chunk_text(self, chunk_service):
        """Test updating chunk text."""
        chunk = await chunk_service.create_chunk(
            document_id="doc1",
            text="Original text",
            start_position=0,
            end_position=13,
        )

        updated = await chunk_service.update_chunk(chunk.id, text="Updated text")

        assert updated is not None
        assert updated.text == "Updated text"

    @pytest.mark.asyncio
    async def test_update_chunk_quality_score(self, chunk_service):
        """Test updating chunk quality score."""
        chunk = await chunk_service.create_chunk(
            document_id="doc1",
            text="Text",
            start_position=0,
            end_position=4,
            quality_score=0.5,
        )

        updated = await chunk_service.update_chunk(chunk.id, quality_score=0.9)

        assert updated.metadata.quality_score == 0.9
        assert updated.metadata.quality_level == ChunkQualityLevel.HIGH

    @pytest.mark.asyncio
    async def test_update_chunk_section(self, chunk_service):
        """Test updating chunk section."""
        chunk = await chunk_service.create_chunk(
            document_id="doc1",
            text="Text",
            start_position=0,
            end_position=4,
            section="OldSection",
        )

        updated = await chunk_service.update_chunk(chunk.id, section="NewSection")

        assert updated.metadata.section == "NewSection"

    @pytest.mark.asyncio
    async def test_update_nonexistent_chunk_returns_none(self, chunk_service):
        """Test updating nonexistent chunk returns None."""
        result = await chunk_service.update_chunk("nonexistent", text="New text")
        assert result is None


class TestChunkDeletion:
    """Tests for chunk deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_chunk(self, chunk_service):
        """Test deleting a chunk."""
        chunk = await chunk_service.create_chunk(
            document_id="doc1",
            text="Text",
            start_position=0,
            end_position=4,
        )

        result = await chunk_service.delete_chunk(chunk.id)

        assert result is True

        # Verify it's deleted
        retrieved = await chunk_service.get_chunk(chunk.id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_chunk_returns_false(self, chunk_service):
        """Test deleting nonexistent chunk returns False."""
        result = await chunk_service.delete_chunk("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_document_chunks(self, chunk_service):
        """Test deleting all chunks for a document."""
        # Create multiple chunks
        for i in range(5):
            await chunk_service.create_chunk(
                document_id="doc1",
                text=f"Chunk {i}",
                start_position=i * 10,
                end_position=(i + 1) * 10,
            )

        # Create chunks for another document
        for i in range(3):
            await chunk_service.create_chunk(
                document_id="doc2",
                text=f"Chunk {i}",
                start_position=i * 10,
                end_position=(i + 1) * 10,
            )

        # Delete doc1 chunks
        deleted_count = await chunk_service.delete_document_chunks("doc1")

        assert deleted_count == 5

        # Verify doc1 chunks are gone
        chunks, total = await chunk_service.get_chunks_by_document("doc1")
        assert len(chunks) == 0

        # Verify doc2 chunks still exist
        chunks, total = await chunk_service.get_chunks_by_document("doc2")
        assert len(chunks) == 3

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document_chunks(self, chunk_service):
        """Test deleting chunks for nonexistent document."""
        deleted_count = await chunk_service.delete_document_chunks("nonexistent")
        assert deleted_count == 0


class TestChunkSearch:
    """Tests for chunk search functionality."""

    @pytest.mark.asyncio
    async def test_search_by_text_query(self, chunk_service):
        """Test text-based chunk search."""
        await chunk_service.create_chunk(
            document_id="doc1",
            text="Hello world example",
            start_position=0,
            end_position=19,
        )
        await chunk_service.create_chunk(
            document_id="doc1",
            text="Goodbye world",
            start_position=19,
            end_position=32,
        )

        results, total = await chunk_service.search_chunks(query="Hello")

        assert len(results) == 1
        assert results[0].text == "Hello world example"

    @pytest.mark.asyncio
    async def test_search_by_document_id(self, chunk_service):
        """Test search filtered by document ID."""
        await chunk_service.create_chunk(
            document_id="doc1", text="Text 1", start_position=0, end_position=6
        )
        await chunk_service.create_chunk(
            document_id="doc2", text="Text 2", start_position=0, end_position=6
        )

        results, total = await chunk_service.search_chunks(document_id="doc1")

        assert len(results) == 1
        assert results[0].document_id == "doc1"

    @pytest.mark.asyncio
    async def test_search_by_quality_score(self, chunk_service):
        """Test search filtered by minimum quality score."""
        await chunk_service.create_chunk(
            document_id="doc1",
            text="Good quality",
            start_position=0,
            end_position=12,
            quality_score=0.9,
        )
        await chunk_service.create_chunk(
            document_id="doc1",
            text="Poor quality",
            start_position=12,
            end_position=24,
            quality_score=0.3,
        )

        results, total = await chunk_service.search_chunks(min_quality_score=0.8)

        assert len(results) == 1
        assert results[0].text == "Good quality"

    @pytest.mark.asyncio
    async def test_search_by_section(self, chunk_service):
        """Test search filtered by section."""
        await chunk_service.create_chunk(
            document_id="doc1",
            text="Intro",
            start_position=0,
            end_position=5,
            section="Introduction",
        )
        await chunk_service.create_chunk(
            document_id="doc1",
            text="Body",
            start_position=5,
            end_position=9,
            section="Body",
        )

        results, total = await chunk_service.search_chunks(section="Introduction")

        assert len(results) == 1
        assert results[0].metadata.section == "Introduction"

    @pytest.mark.asyncio
    async def test_search_by_language(self, chunk_service):
        """Test search filtered by language."""
        await chunk_service.create_chunk(
            document_id="doc1",
            text="English text",
            start_position=0,
            end_position=12,
            language="en",
        )
        await chunk_service.create_chunk(
            document_id="doc1",
            text="Texto español",
            start_position=12,
            end_position=25,
            language="es",
        )

        results, total = await chunk_service.search_chunks(language="en")

        assert len(results) == 1
        assert results[0].metadata.language == "en"

    @pytest.mark.asyncio
    async def test_search_combined_filters(self, chunk_service):
        """Test search with multiple filters combined."""
        await chunk_service.create_chunk(
            document_id="doc1",
            text="High quality intro",
            start_position=0,
            end_position=18,
            section="Introduction",
            quality_score=0.9,
            language="en",
        )
        await chunk_service.create_chunk(
            document_id="doc1",
            text="Low quality body",
            start_position=18,
            end_position=33,
            section="Body",
            quality_score=0.3,
            language="en",
        )

        results, total = await chunk_service.search_chunks(
            section="Introduction", min_quality_score=0.8
        )

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_pagination(self, chunk_service):
        """Test search result pagination."""
        # Create 25 chunks
        for i in range(25):
            await chunk_service.create_chunk(
                document_id="doc1",
                text=f"Chunk {i}",
                start_position=i * 10,
                end_position=(i + 1) * 10,
            )

        results1, total1 = await chunk_service.search_chunks(limit=10, offset=0)
        results2, total2 = await chunk_service.search_chunks(limit=10, offset=10)

        assert len(results1) == 10
        assert len(results2) == 10
        assert total1 == 25
        assert total2 == 25


class TestChunkStatistics:
    """Tests for chunk statistics."""

    @pytest.mark.asyncio
    async def test_get_chunk_count(self, chunk_service):
        """Test getting total chunk count."""
        for i in range(5):
            await chunk_service.create_chunk(
                document_id="doc1",
                text=f"Chunk {i}",
                start_position=i * 10,
                end_position=(i + 1) * 10,
            )

        count = await chunk_service.get_chunk_count()
        assert count == 5

    @pytest.mark.asyncio
    async def test_get_document_chunk_count(self, chunk_service):
        """Test getting chunk count for specific document."""
        for i in range(3):
            await chunk_service.create_chunk(
                document_id="doc1",
                text=f"Chunk {i}",
                start_position=i * 10,
                end_position=(i + 1) * 10,
            )

        for i in range(2):
            await chunk_service.create_chunk(
                document_id="doc2",
                text=f"Chunk {i}",
                start_position=i * 10,
                end_position=(i + 1) * 10,
            )

        count1 = await chunk_service.get_chunk_count(document_id="doc1")
        count2 = await chunk_service.get_chunk_count(document_id="doc2")

        assert count1 == 3
        assert count2 == 2

    @pytest.mark.asyncio
    async def test_get_statistics(self, chunk_service):
        """Test getting chunk statistics."""
        # Create chunks with varying sizes and quality
        for i in range(5):
            await chunk_service.create_chunk(
                document_id="doc1",
                text="Text " * (i + 1),
                start_position=i * 20,
                end_position=(i + 1) * 20,
                quality_score=0.5 + (i * 0.1),
                language="en",
            )

        stats = await chunk_service.get_statistics(document_id="doc1")

        assert stats["total_chunks"] == 5
        assert stats["avg_chunk_size"] > 0
        assert stats["avg_quality_score"] > 0
        assert "quality_distribution" in stats
        assert "language_distribution" in stats

    @pytest.mark.asyncio
    async def test_statistics_empty_service(self, chunk_service):
        """Test statistics for empty chunk service."""
        stats = await chunk_service.get_statistics()

        assert stats["total_chunks"] == 0
        assert stats["avg_chunk_size"] == 0
        assert stats["avg_quality_score"] == 0.0
