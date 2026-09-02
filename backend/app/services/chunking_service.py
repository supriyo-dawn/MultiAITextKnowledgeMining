"""
Text chunking service with multiple strategies.

Implements different chunking approaches:
- Fixed-size: Chunks of fixed character length
- Semantic Sentence-based: Chunks grouped by sentences
- Sliding Window: Overlapping fixed-size chunks
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from app.models.chunk import ChunkingStrategy
from app.services.preprocessing_service import TextPreprocessor

logger = logging.getLogger(__name__)


class ChunkingError(Exception):
    """Exception raised during text chunking."""

    pass


class ChunkingStrategy_Base(ABC):
    """Base class for chunking strategies."""

    def __init__(self, preprocessor: Optional[TextPreprocessor] = None):
        """Initialize chunking strategy with optional preprocessor."""
        self.preprocessor = preprocessor or TextPreprocessor()
        self.logger = logger

    @abstractmethod
    def chunk(
        self, text: str, document_id: str, section: Optional[str] = None, **kwargs
    ) -> list[dict]:
        """
        Chunk text according to strategy.

        Args:
            text: Raw text to chunk
            document_id: Parent document ID
            section: Optional document section/heading
            **kwargs: Strategy-specific parameters

        Returns:
            List of chunk dictionaries with text and metadata
        """
        pass


class FixedSizeChunking(ChunkingStrategy_Base):
    """
    Fixed-size chunking strategy.

    Splits text into chunks of fixed character length with optional overlap.
    Attempts to break at sentence boundaries when possible.
    """

    def chunk(
        self,
        text: str,
        document_id: str,
        section: Optional[str] = None,
        chunk_size: int = 512,
        overlap: int = 50,
        **kwargs,
    ) -> list[dict]:
        """
        Chunk text using fixed size with optional overlap.

        Args:
            text: Raw text to chunk
            document_id: Parent document ID
            section: Optional section name
            chunk_size: Target chunk size in characters (default: 512)
            overlap: Number of characters to overlap between chunks (default: 50)
            **kwargs: Additional parameters

        Returns:
            List of chunk dictionaries
        """
        if not text:
            self.logger.warning("Empty text provided to fixed-size chunking")
            return []

        if chunk_size <= 0:
            raise ChunkingError(f"chunk_size must be positive, got {chunk_size}")

        if overlap >= chunk_size:
            raise ChunkingError(
                f"overlap ({overlap}) must be less than chunk_size ({chunk_size})"
            )

        chunks = []
        text_length = len(text)
        step = chunk_size - overlap

        # Extract sentences for breaking points
        sentences = self.preprocessor.extract_sentences(text)

        pos = 0
        chunk_index = 0

        while pos < text_length:
            # Calculate chunk end position
            chunk_end = min(pos + chunk_size, text_length)

            # Try to break at sentence boundary near chunk_end
            break_pos = self._find_sentence_boundary(text, pos, chunk_end, sentences)

            # Extract chunk text
            chunk_text = text[pos : break_pos if break_pos else chunk_end].strip()

            if chunk_text:
                # Calculate actual statistics
                stats = self.preprocessor.get_text_statistics(chunk_text)

                chunk_dict = {
                    "text": chunk_text,
                    "start_position": pos,
                    "end_position": break_pos if break_pos else chunk_end,
                    "sentence_count": stats.get("sentences", 1),
                    "token_count": self.preprocessor.estimate_token_count(chunk_text),
                    "document_id": document_id,
                    "section": section,
                    "paragraph_index": self._calculate_paragraph_index(text, pos),
                    "chunking_strategy": "fixed_size",
                }

                chunks.append(chunk_dict)
                chunk_index += 1

                # Move position for next chunk
                pos = break_pos if break_pos else chunk_end
                if overlap > 0 and pos < text_length:
                    pos = max(pos - overlap, pos - step + step)
            else:
                break

        self.logger.info(
            f"Fixed-size chunking: {len(chunks)} chunks from {text_length} chars "
            f"(chunk_size={chunk_size}, overlap={overlap})"
        )

        return chunks

    def _find_sentence_boundary(
        self, text: str, start: int, end: int, sentences: list[str]
    ) -> Optional[int]:
        """Find a good break point near 'end' that aligns with sentence boundary."""
        # Simple search: find the last period/! /? before 'end'
        for i in range(min(end, len(text)) - 1, start - 1, -1):
            if text[i] in ".!?":
                # Check if it's followed by space or end of text
                if i + 1 >= len(text) or text[i + 1] in " \n":
                    return i + 1

        return None

    def _calculate_paragraph_index(self, text: str, position: int) -> int:
        """Calculate which paragraph the position falls into."""
        # Count paragraphs before position
        return len(text[:position].split("\n\n"))


class SemanticSentenceChunking(ChunkingStrategy_Base):
    """
    Semantic sentence-based chunking.

    Groups sentences together to form chunks, attempting to reach target size
    while respecting semantic boundaries.
    """

    def chunk(
        self,
        text: str,
        document_id: str,
        section: Optional[str] = None,
        target_chunk_size: int = 512,
        **kwargs,
    ) -> list[dict]:
        """
        Chunk text by grouping sentences.

        Args:
            text: Raw text to chunk
            document_id: Parent document ID
            section: Optional section name
            target_chunk_size: Target chunk size in characters (default: 512)
            **kwargs: Additional parameters

        Returns:
            List of chunk dictionaries
        """
        if not text:
            self.logger.warning("Empty text provided to sentence-based chunking")
            return []

        # Extract sentences
        sentences = self.preprocessor.extract_sentences(text)

        if not sentences:
            self.logger.warning("No sentences found in text")
            return []

        chunks = []
        current_chunk = []
        current_size = 0
        chunk_start_pos = 0

        for sentence_idx, sentence in enumerate(sentences):
            sentence_len = len(sentence)

            # Add sentence to current chunk if it fits
            if current_size + sentence_len <= target_chunk_size or not current_chunk:
                current_chunk.append(sentence)
                current_size += sentence_len + 1  # +1 for space

            else:
                # Finalize current chunk
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunk_start_pos = self._find_position_in_text(text, chunk_text)

                    chunk_dict = {
                        "text": chunk_text,
                        "start_position": chunk_start_pos,
                        "end_position": chunk_start_pos + len(chunk_text),
                        "sentence_count": len(current_chunk),
                        "token_count": self.preprocessor.estimate_token_count(chunk_text),
                        "document_id": document_id,
                        "section": section,
                        "paragraph_index": self._calculate_paragraph_index(text, chunk_start_pos),
                        "chunking_strategy": "semantic_sentence",
                    }

                    chunks.append(chunk_dict)

                # Start new chunk with current sentence
                current_chunk = [sentence]
                current_size = sentence_len

        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_start_pos = self._find_position_in_text(text, chunk_text)

            chunk_dict = {
                "text": chunk_text,
                "start_position": chunk_start_pos,
                "end_position": chunk_start_pos + len(chunk_text),
                "sentence_count": len(current_chunk),
                "token_count": self.preprocessor.estimate_token_count(chunk_text),
                "document_id": document_id,
                "section": section,
                "paragraph_index": self._calculate_paragraph_index(text, chunk_start_pos),
                "chunking_strategy": "semantic_sentence",
            }

            chunks.append(chunk_dict)

        self.logger.info(
            f"Semantic sentence chunking: {len(chunks)} chunks from "
            f"{len(sentences)} sentences"
        )

        return chunks

    def _find_position_in_text(self, text: str, substring: str) -> int:
        """Find approximate position of substring in text."""
        pos = text.find(substring)
        return max(0, pos) if pos != -1 else 0

    def _calculate_paragraph_index(self, text: str, position: int) -> int:
        """Calculate which paragraph the position falls into."""
        return len(text[:position].split("\n\n"))


class SlidingWindowChunking(ChunkingStrategy_Base):
    """
    Sliding window chunking strategy.

    Creates fixed-size chunks with a sliding window approach,
    ensuring all content is captured with overlap.
    """

    def chunk(
        self,
        text: str,
        document_id: str,
        section: Optional[str] = None,
        chunk_size: int = 512,
        overlap: int = 50,
        **kwargs,
    ) -> list[dict]:
        """
        Chunk text using sliding window.

        Args:
            text: Raw text to chunk
            document_id: Parent document ID
            section: Optional section name
            chunk_size: Window size in characters (default: 512)
            overlap: Number of overlapping characters (default: 50)
            **kwargs: Additional parameters

        Returns:
            List of chunk dictionaries
        """
        if not text:
            self.logger.warning("Empty text provided to sliding window chunking")
            return []

        if chunk_size <= 0:
            raise ChunkingError(f"chunk_size must be positive, got {chunk_size}")

        if overlap >= chunk_size:
            raise ChunkingError(
                f"overlap ({overlap}) must be less than chunk_size ({chunk_size})"
            )

        chunks = []
        step = chunk_size - overlap
        text_length = len(text)

        pos = 0
        while pos < text_length:
            # Calculate window
            chunk_end = min(pos + chunk_size, text_length)

            # Extract chunk
            chunk_text = text[pos:chunk_end].strip()

            if chunk_text:
                # Calculate statistics
                stats = self.preprocessor.get_text_statistics(chunk_text)

                chunk_dict = {
                    "text": chunk_text,
                    "start_position": pos,
                    "end_position": chunk_end,
                    "sentence_count": stats.get("sentences", 1),
                    "token_count": self.preprocessor.estimate_token_count(chunk_text),
                    "document_id": document_id,
                    "section": section,
                    "paragraph_index": self._calculate_paragraph_index(text, pos),
                    "chunking_strategy": "sliding_window",
                }

                chunks.append(chunk_dict)

            # Move window forward
            pos += step

        self.logger.info(
            f"Sliding window chunking: {len(chunks)} chunks from {text_length} chars "
            f"(chunk_size={chunk_size}, overlap={overlap})"
        )

        return chunks

    def _calculate_paragraph_index(self, text: str, position: int) -> int:
        """Calculate which paragraph the position falls into."""
        return len(text[:position].split("\n\n"))


class TextChunker:
    """
    Main text chunking service.

    Coordinates different chunking strategies and manages preprocessing.
    """

    def __init__(self):
        """Initialize the text chunker."""
        self.preprocessor = TextPreprocessor()
        self.strategies = {
            "fixed_size": FixedSizeChunking(self.preprocessor),
            "semantic_sentence": SemanticSentenceChunking(self.preprocessor),
            "sliding_window": SlidingWindowChunking(self.preprocessor),
        }
        self.logger = logger

    def chunk_text(
        self,
        text: str,
        document_id: str,
        strategy: str = "fixed_size",
        section: Optional[str] = None,
        preprocess: bool = True,
        detect_language: bool = True,
        **strategy_kwargs,
    ) -> list[dict]:
        """
        Chunk text using specified strategy.

        Args:
            text: Raw text to chunk
            document_id: Parent document ID
            strategy: Chunking strategy name (default: 'fixed_size')
            section: Optional document section
            preprocess: Whether to preprocess text first (default: True)
            detect_language: Whether to detect language during preprocessing
            **strategy_kwargs: Strategy-specific parameters

        Returns:
            List of chunk dictionaries with text and metadata

        Raises:
            ChunkingError: If chunking fails
        """
        try:
            if not text:
                raise ChunkingError("Text cannot be empty")

            if strategy not in self.strategies:
                raise ChunkingError(
                    f"Unknown strategy '{strategy}'. "
                    f"Available: {list(self.strategies.keys())}"
                )

            # Preprocess if requested
            language = None
            if preprocess:
                result = self.preprocessor.preprocess(
                    text, detect_language=detect_language
                )
                text = result["text"]
                language = result["language"]

            # Apply chunking strategy
            chunker = self.strategies[strategy]
            chunks = chunker.chunk(
                text, document_id=document_id, section=section, **strategy_kwargs
            )

            # Enrich chunks with language and quality scoring
            for chunk in chunks:
                if language:
                    chunk["language"] = language

                # Calculate quality score based on heuristics
                chunk["quality_score"] = self._calculate_quality_score(chunk)

            self.logger.info(
                f"Text chunking complete: {len(chunks)} chunks "
                f"(strategy={strategy}, language={language})"
            )

            return chunks

        except ChunkingError:
            raise
        except Exception as e:
            self.logger.error(f"Chunking error: {str(e)}")
            raise ChunkingError(f"Failed to chunk text: {str(e)}") from e

    def _calculate_quality_score(self, chunk: dict) -> float:
        """
        Calculate quality score for a chunk.

        Quality is based on:
        - Length (prefer chunks near target size)
        - Sentence count (prefer complete sentences)
        - Token count (prefer properly tokenized content)

        Returns float between 0 and 1.
        """
        score = 0.5  # Base score

        # Reward for appropriate length (256-768 characters is good)
        text_len = len(chunk["text"])
        if 256 <= text_len <= 768:
            score += 0.3
        elif 128 <= text_len < 256 or 768 < text_len <= 1024:
            score += 0.15
        else:
            score -= 0.1

        # Reward for multiple complete sentences
        sentence_count = chunk.get("sentence_count", 1)
        if sentence_count >= 2:
            score += 0.15
        elif sentence_count == 1 and text_len > 100:
            score += 0.05

        # Reward for proper tokenization
        token_count = chunk.get("token_count", 0)
        if 20 <= token_count <= 300:
            score += 0.05

        # Clamp score to 0-1 range
        return max(0.0, min(1.0, score))
