"""
Text preprocessing service for advanced text cleaning and normalization.

Provides preprocessing capabilities including:
- Advanced text cleaning (control chars, special entities, etc.)
- Language detection
- Format preservation
- Text normalization
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class PreprocessingError(Exception):
    """Exception raised during text preprocessing."""

    pass


class TextPreprocessor:
    """
    Advanced text preprocessing service.

    Handles text cleaning, language detection, and normalization
    while preserving document structure and formatting.
    """

    # Language detection simple heuristics (Unicode ranges)
    LANGUAGE_PATTERNS = {
        "en": r"[a-zA-Z]",  # English
        "es": r"[a-záéíóúñ]",  # Spanish
        "fr": r"[a-zàâäçèéêëîïôùûüœæ]",  # French
        "de": r"[a-zäöüß]",  # German
        "zh": r"[\u4E00-\u9FFF]",  # Chinese
        "ar": r"[\u0600-\u06FF]",  # Arabic
        "ru": r"[\u0400-\u04FF]",  # Russian
        "ja": r"[\u3040-\u309F\u30A0-\u30FF]",  # Japanese
    }

    def __init__(self):
        """Initialize the text preprocessor."""
        self.logger = logger

    def preprocess(
        self,
        text: str,
        normalize: bool = True,
        detect_language: bool = True,
        remove_urls: bool = True,
        remove_emails: bool = False,
    ) -> dict:
        """
        Preprocess text with comprehensive cleaning and enrichment.

        Args:
            text: Raw text to preprocess
            normalize: Whether to normalize whitespace
            detect_language: Whether to detect language
            remove_urls: Whether to remove URLs
            remove_emails: Whether to remove email addresses

        Returns:
            Dictionary with cleaned_text, language, and preprocessing metadata

        Raises:
            PreprocessingError: If preprocessing fails
        """
        try:
            if not text or not isinstance(text, str):
                raise PreprocessingError("Text must be non-empty string")

            # Store original length for metrics
            original_length = len(text)

            # Step 1: Remove URLs if requested
            if remove_urls:
                text = self._remove_urls(text)

            # Step 2: Remove email addresses if requested
            if remove_emails:
                text = self._remove_emails(text)

            # Step 3: Remove control characters and invisible Unicode
            text = self._remove_control_characters(text)

            # Step 4: Normalize HTML entities
            text = self._normalize_entities(text)

            # Step 5: Normalize whitespace if requested
            if normalize:
                text = self._normalize_whitespace(text)

            # Step 6: Detect language if requested
            language = None
            if detect_language:
                language = self._detect_language(text)

            # Step 7: Calculate preprocessing metrics
            cleaned_length = len(text)
            removed_chars = original_length - cleaned_length

            self.logger.info(
                f"Preprocessing complete: {cleaned_length} chars "
                f"(removed {removed_chars}), lang={language}"
            )

            return {
                "text": text,
                "language": language,
                "original_length": original_length,
                "cleaned_length": cleaned_length,
                "removed_chars": removed_chars,
                "normalized": normalize,
                "urls_removed": remove_urls,
                "emails_removed": remove_emails,
            }

        except PreprocessingError:
            raise
        except Exception as e:
            self.logger.error(f"Preprocessing error: {str(e)}")
            raise PreprocessingError(f"Failed to preprocess text: {str(e)}") from e

    def _remove_urls(self, text: str) -> str:
        """Remove URLs from text while preserving surrounding text."""
        # Match http(s)://, ftp://, or www.
        url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        text = re.sub(url_pattern, " ", text)

        # Match www. URLs
        www_pattern = r"www\.[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}"
        text = re.sub(www_pattern, " ", text)

        return text

    def _remove_emails(self, text: str) -> str:
        """Remove email addresses from text."""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        return re.sub(email_pattern, " ", text)

    def _remove_control_characters(self, text: str) -> str:
        """
        Remove control characters and invisible Unicode characters.

        Preserves common whitespace like newlines and tabs.
        """
        # Remove null bytes and other control characters except \n, \r, \t
        cleaned = ""
        for char in text:
            code_point = ord(char)
            # Allow: space (32), tab (9), newline (10), carriage return (13)
            # and visible characters (code_point >= 32)
            if code_point >= 32 or char in "\n\r\t":
                cleaned += char

        return cleaned

    def _normalize_entities(self, text: str) -> str:
        """Normalize HTML entities and special character sequences."""
        # Common HTML entities
        entities = {
            "&nbsp;": " ",
            "&quot;": '"',
            "&apos;": "'",
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&ndash;": "–",
            "&mdash;": "—",
            "&ldquo;": """,
            "&rdquo;": """,
            "&lsquo;": "'",
            "&rsquo;": "'",
            "&hellip;": "…",
        }

        for entity, replacement in entities.items():
            text = text.replace(entity, replacement)

        return text

    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace while preserving paragraph structure.

        - Multiple spaces → single space
        - Multiple newlines → preserved (for paragraph detection)
        - Leading/trailing whitespace per line → removed
        """
        # Normalize spaces within lines
        lines = text.split("\n")
        normalized_lines = []

        for line in lines:
            # Remove leading/trailing whitespace
            line = line.strip()
            # Collapse multiple spaces to single space
            line = re.sub(r" +", " ", line)
            if line:  # Only add non-empty lines
                normalized_lines.append(line)

        # Join with single newline, allowing empty lines to be filtered
        text = "\n".join(normalized_lines)

        return text

    def _detect_language(self, text: str) -> Optional[str]:
        """
        Detect language using character pattern heuristics.

        Returns ISO 639-1 language code or None if undetected.
        This is a simple heuristic-based approach suitable for Phase 3.
        For production use, consider using langdetect or textblob.
        """
        if not text or len(text) < 10:
            return None

        text_lower = text.lower()
        scores = {}

        # Score each language based on character pattern matches
        for language, pattern in self.LANGUAGE_PATTERNS.items():
            matches = len(re.findall(pattern, text_lower))
            if matches > 0:
                scores[language] = matches

        if not scores:
            return None

        # Return language with highest score
        detected = max(scores, key=scores.get)
        self.logger.debug(f"Language detection scores: {scores}, detected: {detected}")

        return detected

    def clean_text_simple(self, text: str) -> str:
        """
        Simple text cleaning (backward compatible with Phase 2 utils.text.clean_text).

        Removes control characters and normalizes whitespace.
        """
        result = self.preprocess(
            text,
            normalize=True,
            detect_language=False,
            remove_urls=False,
            remove_emails=False,
        )
        return result["text"]

    def extract_sentences(self, text: str) -> list[str]:
        """
        Extract sentences from text using regex-based splitting.

        Handles common abbreviations and preserves sentence boundaries.
        """
        if not text:
            return []

        # Split on sentence boundaries: . ! ? followed by space and capital letter
        # Also handles ellipsis (...)
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)

        # Clean up empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def get_text_statistics(self, text: str) -> dict:
        """
        Get text statistics (compatible with Phase 2 utils.text.get_text_statistics).

        Returns character, word, line, and paragraph counts.
        """
        if not text:
            return {
                "characters": 0,
                "words": 0,
                "lines": 0,
                "paragraphs": 0,
                "sentences": 0,
            }

        # Count characters
        char_count = len(text)

        # Count words (simple split on whitespace)
        word_count = len(text.split())

        # Count lines
        line_count = len(text.split("\n"))

        # Count paragraphs (separated by double newline or empty line)
        paragraph_count = len([p for p in text.split("\n\n") if p.strip()])

        # Count sentences
        sentences = self.extract_sentences(text)
        sentence_count = len(sentences)

        return {
            "characters": char_count,
            "words": word_count,
            "lines": line_count,
            "paragraphs": paragraph_count,
            "sentences": sentence_count,
        }

    def estimate_token_count(self, text: str, language: Optional[str] = None) -> int:
        """
        Estimate token count using simple heuristic.

        Different languages have different token-to-word ratios.
        This is a rough estimate; actual token count depends on tokenizer.

        For English: ~1.3 tokens per word on average (GPT tokenizer)
        For CJK: ~0.8 words per character (already pre-segmented)
        """
        if not text:
            return 0

        words = len(text.split())

        # Adjust for language
        if language in ["zh", "ja", "ar"]:
            # CJK and RTL languages need character-based estimation
            return max(words, len(text) // 3)  # Rough estimate
        else:
            # European languages: ~1.3 tokens per word
            return int(words * 1.3)
