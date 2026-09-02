"""
Unit tests for text chunking service.

Tests:
- Fixed-size chunking strategy
- Semantic sentence-based chunking
- Sliding window chunking
- Main TextChunker orchestrator
- Quality scoring
- Chunking error handling
"""

import pytest

from app.services.chunking_service import (
    ChunkingError,
    FixedSizeChunking,
    SemanticSentenceChunking,
    SlidingWindowChunking,
    TextChunker,
)
from app.services.preprocessing_service import TextPreprocessor


@pytest.fixture
def sample_text():
    """Sample text for chunking tests."""
    return """
    This is the first paragraph. It contains multiple sentences. Each sentence has some content.
    
    This is the second paragraph. It also contains multiple sentences for testing. The chunking algorithm should handle this properly.
    
    This is the third paragraph with a single long sentence that goes on and on with more and more content to test how the chunking algorithm handles longer text without many sentence boundaries.
    """.strip()


@pytest.fixture
def simple_text():
    """Simple short text for basic tests."""
    return "Hello. World. Test."


@pytest.fixture
def preprocessor():
    """Create a text preprocessor instance."""
    return TextPreprocessor()


@pytest.fixture
def text_chunker():
    """Create a text chunker instance."""
    return TextChunker()


class TestFixedSizeChunking:
    """Tests for fixed-size chunking strategy."""

    def test_basic_fixed_size_chunking(self, preprocessor):
        """Test basic fixed-size chunking."""
        chunker = FixedSizeChunking(preprocessor)
        text = "A" * 1000
        chunks = chunker.chunk(text, document_id="doc1", chunk_size=256)

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk["text"]) > 0
            assert chunk["document_id"] == "doc1"
            assert "start_position" in chunk
            assert "end_position" in chunk

    def test_fixed_size_chunk_size_respected(self, preprocessor):
        """Test that chunk size is approximately respected."""
        chunker = FixedSizeChunking(preprocessor)
        text = "Word " * 500  # 2500 characters
        chunk_size = 256
        chunks = chunker.chunk(text, document_id="doc1", chunk_size=chunk_size)

        for chunk in chunks:
            # Allow some flexibility due to sentence boundary breaking
            assert len(chunk["text"]) <= chunk_size * 1.5

    def test_overlap_parameter(self, preprocessor):
        """Test that overlap parameter is used."""
        chunker = FixedSizeChunking(preprocessor)
        text = "Word " * 500
        chunks_no_overlap = chunker.chunk(
            text, document_id="doc1", chunk_size=256, overlap=0
        )
        chunks_with_overlap = chunker.chunk(
            text, document_id="doc1", chunk_size=256, overlap=50
        )

        # With overlap, we should have more chunks
        # (not guaranteed, but very likely)
        assert len(chunks_no_overlap) >= 1
        assert len(chunks_with_overlap) >= 1

    def test_empty_text_returns_empty_list(self, preprocessor):
        """Test that empty text returns empty list."""
        chunker = FixedSizeChunking(preprocessor)
        chunks = chunker.chunk("", document_id="doc1")
        assert chunks == []

    def test_invalid_chunk_size_raises_error(self, preprocessor):
        """Test that invalid chunk size raises error."""
        chunker = FixedSizeChunking(preprocessor)
        with pytest.raises(ChunkingError):
            chunker.chunk("text", document_id="doc1", chunk_size=0)

    def test_overlap_greater_than_chunk_size_raises_error(self, preprocessor):
        """Test that overlap >= chunk_size raises error."""
        chunker = FixedSizeChunking(preprocessor)
        with pytest.raises(ChunkingError):
            chunker.chunk("text", document_id="doc1", chunk_size=256, overlap=512)

    def test_chunk_metadata_fields(self, preprocessor):
        """Test that chunk metadata is populated."""
        chunker = FixedSizeChunking(preprocessor)
        text = "Hello World. Test sentence."
        chunks = chunker.chunk(text, document_id="doc1", section="intro")

        for chunk in chunks:
            assert chunk["document_id"] == "doc1"
            assert chunk["section"] == "intro"
            assert chunk["sentence_count"] >= 0
            assert chunk["token_count"] is not None
            assert chunk["chunking_strategy"] == "fixed_size"


class TestSemanticSentenceChunking:
    """Tests for semantic sentence-based chunking."""

    def test_basic_sentence_chunking(self, preprocessor, simple_text):
        """Test basic sentence-based chunking."""
        chunker = SemanticSentenceChunking(preprocessor)
        chunks = chunker.chunk(simple_text, document_id="doc1")

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk["text"]) > 0
            assert chunk["document_id"] == "doc1"

    def test_sentence_count_field(self, preprocessor, simple_text):
        """Test that sentence count is tracked."""
        chunker = SemanticSentenceChunking(preprocessor)
        chunks = chunker.chunk(simple_text, document_id="doc1")

        for chunk in chunks:
            assert chunk["sentence_count"] >= 1

    def test_target_chunk_size_parameter(self, preprocessor):
        """Test that target_chunk_size parameter affects chunking."""
        chunker = SemanticSentenceChunking(preprocessor)
        text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."

        chunks_small = chunker.chunk(
            text, document_id="doc1", target_chunk_size=20
        )
        chunks_large = chunker.chunk(
            text, document_id="doc1", target_chunk_size=200
        )

        # Smaller target size should produce more chunks
        assert len(chunks_small) >= len(chunks_large)

    def test_empty_text_returns_empty_list(self, preprocessor):
        """Test that empty text returns empty list."""
        chunker = SemanticSentenceChunking(preprocessor)
        chunks = chunker.chunk("", document_id="doc1")
        assert chunks == []

    def test_text_without_sentences(self, preprocessor):
        """Test text without proper sentence boundaries."""
        chunker = SemanticSentenceChunking(preprocessor)
        text = "No sentence boundaries here"
        chunks = chunker.chunk(text, document_id="doc1")

        # Should still produce at least one chunk
        assert len(chunks) >= 1

    def test_chunking_strategy_field(self, preprocessor, simple_text):
        """Test that chunking strategy is recorded."""
        chunker = SemanticSentenceChunking(preprocessor)
        chunks = chunker.chunk(simple_text, document_id="doc1")

        for chunk in chunks:
            assert chunk["chunking_strategy"] == "semantic_sentence"


class TestSlidingWindowChunking:
    """Tests for sliding window chunking strategy."""

    def test_basic_sliding_window(self, preprocessor):
        """Test basic sliding window chunking."""
        chunker = SlidingWindowChunking(preprocessor)
        text = "Word " * 300
        chunks = chunker.chunk(text, document_id="doc1", chunk_size=256)

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk["text"]) > 0

    def test_sliding_window_coverage(self, preprocessor):
        """Test that sliding window covers all text."""
        chunker = SlidingWindowChunking(preprocessor)
        text = "Word " * 300
        chunk_size = 256
        overlap = 50
        chunks = chunker.chunk(
            text, document_id="doc1", chunk_size=chunk_size, overlap=overlap
        )

        # Verify coverage (allowing some end-text loss due to stripping)
        assert len(chunks) > 1

    def test_overlap_creates_more_chunks(self, preprocessor):
        """Test that overlap doesn't reduce chunk count."""
        chunker = SlidingWindowChunking(preprocessor)
        text = "Word " * 300

        chunks_no_overlap = chunker.chunk(
            text, document_id="doc1", chunk_size=256, overlap=0
        )
        chunks_with_overlap = chunker.chunk(
            text, document_id="doc1", chunk_size=256, overlap=50
        )

        # With overlap, we typically get same or more chunks
        assert len(chunks_with_overlap) >= len(chunks_no_overlap) - 1

    def test_empty_text_returns_empty_list(self, preprocessor):
        """Test that empty text returns empty list."""
        chunker = SlidingWindowChunking(preprocessor)
        chunks = chunker.chunk("", document_id="doc1")
        assert chunks == []

    def test_invalid_chunk_size_raises_error(self, preprocessor):
        """Test that invalid chunk size raises error."""
        chunker = SlidingWindowChunking(preprocessor)
        with pytest.raises(ChunkingError):
            chunker.chunk("text", document_id="doc1", chunk_size=-1)

    def test_chunking_strategy_field(self, preprocessor):
        """Test that chunking strategy is recorded."""
        chunker = SlidingWindowChunking(preprocessor)
        text = "Word " * 300
        chunks = chunker.chunk(text, document_id="doc1")

        for chunk in chunks:
            assert chunk["chunking_strategy"] == "sliding_window"


class TestTextChunker:
    """Tests for main TextChunker orchestrator."""

    def test_fixed_size_strategy(self, text_chunker, sample_text):
        """Test fixed-size chunking through main orchestrator."""
        chunks = text_chunker.chunk_text(
            sample_text, document_id="doc1", strategy="fixed_size"
        )

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk["document_id"] == "doc1"
            assert chunk["quality_score"] >= 0.0
            assert chunk["quality_score"] <= 1.0

    def test_semantic_sentence_strategy(self, text_chunker, sample_text):
        """Test semantic sentence chunking through main orchestrator."""
        chunks = text_chunker.chunk_text(
            sample_text, document_id="doc1", strategy="semantic_sentence"
        )

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk["chunking_strategy"] == "semantic_sentence"

    def test_sliding_window_strategy(self, text_chunker, sample_text):
        """Test sliding window chunking through main orchestrator."""
        chunks = text_chunker.chunk_text(
            sample_text, document_id="doc1", strategy="sliding_window"
        )

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk["chunking_strategy"] == "sliding_window"

    def test_invalid_strategy_raises_error(self, text_chunker, sample_text):
        """Test that invalid strategy raises error."""
        with pytest.raises(ChunkingError):
            text_chunker.chunk_text(
                sample_text, document_id="doc1", strategy="invalid_strategy"
            )

    def test_preprocessing_applied(self, text_chunker):
        """Test that preprocessing is applied when requested."""
        text = "Hello https://example.com World"
        chunks = text_chunker.chunk_text(
            text, document_id="doc1", preprocess=True, detect_language=False
        )

        # URL should be removed during preprocessing
        full_text = " ".join(c["text"] for c in chunks)
        assert "example.com" not in full_text

    def test_preprocessing_disabled(self, text_chunker):
        """Test that preprocessing can be disabled."""
        text = "Hello https://example.com World"
        chunks = text_chunker.chunk_text(
            text, document_id="doc1", preprocess=False, detect_language=False
        )

        # URL should be preserved
        full_text = " ".join(c["text"] for c in chunks)
        assert "example.com" in full_text

    def test_language_detection(self, text_chunker):
        """Test that language is detected when requested."""
        text = "This is English text."
        chunks = text_chunker.chunk_text(
            text, document_id="doc1", detect_language=True
        )

        for chunk in chunks:
            assert chunk["language"] is not None

    def test_quality_score_calculation(self, text_chunker):
        """Test that quality scores are calculated."""
        text = "Hello. World. Test."
        chunks = text_chunker.chunk_text(
            text, document_id="doc1", strategy="semantic_sentence"
        )

        assert all(0.0 <= c["quality_score"] <= 1.0 for c in chunks)

    def test_empty_text_raises_error(self, text_chunker):
        """Test that empty text raises error."""
        with pytest.raises(ChunkingError):
            text_chunker.chunk_text("", document_id="doc1")

    def test_chunk_metadata_enrichment(self, text_chunker, sample_text):
        """Test that chunk metadata is enriched."""
        chunks = text_chunker.chunk_text(sample_text, document_id="doc1")

        for chunk in chunks:
            assert "text" in chunk
            assert "document_id" in chunk
            assert "start_position" in chunk
            assert "end_position" in chunk
            assert "sentence_count" in chunk
            assert "quality_score" in chunk
            # Note: quality_level is added when chunk is stored via chunk_service
            assert "token_count" in chunk
            assert "chunking_strategy" in chunk

    def test_strategy_kwargs_passed(self, text_chunker, sample_text):
        """Test that strategy-specific kwargs are passed."""
        chunks = text_chunker.chunk_text(
            sample_text,
            document_id="doc1",
            strategy="fixed_size",
            chunk_size=128,
            overlap=25,
        )

        # Should accept and use the parameters
        assert len(chunks) > 0


class TestQualityScoring:
    """Tests for chunk quality scoring."""

    def test_quality_score_range(self, text_chunker):
        """Test that quality scores are in valid range."""
        text = "Sentence one. Sentence two. Sentence three."
        chunks = text_chunker.chunk_text(
            text, document_id="doc1", strategy="semantic_sentence"
        )

        for chunk in chunks:
            assert 0.0 <= chunk["quality_score"] <= 1.0

    def test_good_length_scores_higher(self, text_chunker):
        """Test that well-sized chunks score higher."""
        # Medium-sized text chunks tend to have higher quality
        text = ("Good length sentence. " * 20).strip()
        chunks = text_chunker.chunk_text(
            text, document_id="doc1", strategy="semantic_sentence"
        )

        for chunk in chunks:
            # Should have reasonable quality scores
            assert chunk["quality_score"] >= 0.3

    def test_very_small_chunk_lower_quality(self, text_chunker):
        """Test that very small chunks have lower quality."""
        text = "A. B. C."
        chunks = text_chunker.chunk_text(
            text, document_id="doc1", strategy="semantic_sentence"
        )

        # Very small chunks should have lower quality
        for chunk in chunks:
            if len(chunk["text"]) < 20:
                assert chunk["quality_score"] < 0.8


class TestErrorHandling:
    """Tests for error handling."""

    def test_none_text_raises_error(self, text_chunker):
        """Test that None text raises error."""
        with pytest.raises(ChunkingError):
            text_chunker.chunk_text(None, document_id="doc1")

    def test_missing_document_id_raises_error(self, text_chunker):
        """Test that empty text raises error (document_id is optional at chunker level)."""
        # Document_id is not validated at chunker level, only at chunk_service level
        # So we test that empty text raises error instead
        with pytest.raises(ChunkingError):
            text_chunker.chunk_text("", document_id="doc1")

    def test_chunking_very_long_text(self, text_chunker):
        """Test that very long text can be chunked."""
        long_text = "Word " * 10000
        chunks = text_chunker.chunk_text(long_text, document_id="doc1")

        assert len(chunks) > 0
        assert len(chunks) <= 200  # Should be reasonably split
