"""
File validation utilities.
Validates files by content, not by extension (security best practice).
"""

import mimetypes
from pathlib import Path

# Magic bytes (file signatures) for content-based validation
FILE_SIGNATURES = {
    "pdf": b"%PDF",
    "docx": b"PK\x03\x04",  # ZIP format used by DOCX
    "txt": None,  # Text files have no specific signature
}

# Maximum file size (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024


class FileValidationError(Exception):
    """Raised when file validation fails."""

    pass


def get_file_type_from_extension(filename: str) -> str:
    """
    Get file type from filename extension.

    Args:
        filename: The filename to check

    Returns:
        File type: 'pdf', 'docx', 'txt'

    Raises:
        FileValidationError: If file type is not supported
    """
    suffix = Path(filename).suffix.lower().lstrip(".")

    # Map common extensions
    extension_map = {
        "pdf": "pdf",
        "docx": "docx",
        "doc": "docx",  # Older Word format, treat as docx for now
        "txt": "txt",
        "text": "txt",
    }

    file_type = extension_map.get(suffix)
    if not file_type:
        raise FileValidationError(
            f"Unsupported file type: {suffix}. Supported types: pdf, docx, txt"
        )

    return file_type


def validate_file_by_signature(file_content: bytes, expected_type: str) -> bool:
    """
    Validate file content by checking magic bytes (file signature).

    Args:
        file_content: The raw file content
        expected_type: Expected file type ('pdf', 'docx', 'txt')

    Returns:
        True if file signature matches expected type

    Raises:
        FileValidationError: If file signature does not match
    """
    if not file_content:
        raise FileValidationError("File is empty")

    signature = FILE_SIGNATURES.get(expected_type)

    if signature is None:
        # Text files: no strict signature check, but should be readable
        try:
            file_content.decode("utf-8", errors="strict")
            return True
        except UnicodeDecodeError:
            raise FileValidationError(
                f"File appears to be binary, not text ({expected_type})"
            )

    # Check if file starts with expected signature
    if not file_content.startswith(signature):
        raise FileValidationError(
            f"File signature does not match {expected_type} format. "
            f"Expected to start with {signature}, got {file_content[:4]}"
        )

    return True


def validate_file_upload(
    filename: str, file_content: bytes, allowed_types: list[str] = None
) -> tuple[str, int]:
    """
    Validate uploaded file.

    Args:
        filename: Original filename
        file_content: Raw file content
        allowed_types: List of allowed file types (defaults to all)

    Returns:
        Tuple of (file_type, file_size_bytes)

    Raises:
        FileValidationError: If file validation fails
    """
    if allowed_types is None:
        allowed_types = ["pdf", "docx", "txt"]

    # Check file size
    file_size = len(file_content)
    if file_size > MAX_FILE_SIZE:
        raise FileValidationError(
            f"File size ({file_size / 1024 / 1024:.1f} MB) exceeds "
            f"maximum allowed ({MAX_FILE_SIZE / 1024 / 1024:.0f} MB)"
        )

    if file_size == 0:
        raise FileValidationError("File is empty")

    # Get expected file type from extension
    file_type = get_file_type_from_extension(filename)

    # Check if file type is allowed
    if file_type not in allowed_types:
        raise FileValidationError(
            f"File type '{file_type}' is not allowed. "
            f"Allowed types: {', '.join(allowed_types)}"
        )

    # Validate file signature
    validate_file_by_signature(file_content, file_type)

    return file_type, file_size
