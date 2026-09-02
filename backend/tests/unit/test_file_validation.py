"""Unit tests for file validation utilities."""

import pytest

from app.utils.file import (
    FileValidationError,
    get_file_type_from_extension,
    validate_file_by_signature,
    validate_file_upload,
)


class TestGetFileTypeFromExtension:
    """Tests for file type detection from extension."""

    def test_pdf_extension(self):
        """Test PDF file type detection."""
        assert get_file_type_from_extension("document.pdf") == "pdf"
        assert get_file_type_from_extension("DOCUMENT.PDF") == "pdf"

    def test_docx_extension(self):
        """Test DOCX file type detection."""
        assert get_file_type_from_extension("document.docx") == "docx"
        assert get_file_type_from_extension("document.doc") == "docx"

    def test_txt_extension(self):
        """Test TXT file type detection."""
        assert get_file_type_from_extension("document.txt") == "txt"
        assert get_file_type_from_extension("document.text") == "txt"

    def test_unsupported_extension(self):
        """Test unsupported file type raises error."""
        with pytest.raises(FileValidationError) as exc_info:
            get_file_type_from_extension("document.xyz")
        assert "Unsupported file type" in str(exc_info.value)

    def test_no_extension(self):
        """Test file with no extension raises error."""
        with pytest.raises(FileValidationError):
            get_file_type_from_extension("document")


class TestValidateFileBySignature:
    """Tests for file signature validation."""

    def test_valid_pdf_signature(self):
        """Test valid PDF signature."""
        pdf_content = b"%PDF-1.4\nsome pdf content"
        assert validate_file_by_signature(pdf_content, "pdf") is True

    def test_valid_docx_signature(self):
        """Test valid DOCX signature (ZIP format)."""
        docx_content = b"PK\x03\x04some zip content"
        assert validate_file_by_signature(docx_content, "docx") is True

    def test_valid_txt_signature(self):
        """Test valid TXT file."""
        txt_content = "Hello, world!".encode("utf-8")
        assert validate_file_by_signature(txt_content, "txt") is True

    def test_invalid_pdf_signature(self):
        """Test invalid PDF signature."""
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_by_signature(b"Not a PDF file", "pdf")
        assert "File signature does not match" in str(exc_info.value)

    def test_invalid_docx_signature(self):
        """Test invalid DOCX signature."""
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_by_signature(b"Not a DOCX file", "docx")
        assert "File signature does not match" in str(exc_info.value)

    def test_binary_txt_fails(self):
        """Test binary content fails TXT validation."""
        # Use definitely invalid UTF-8 sequence
        binary_content = b"\x80\x81\x82\x83\x84"
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_by_signature(binary_content, "txt")
        assert "binary" in str(exc_info.value).lower()

    def test_empty_file(self):
        """Test empty file raises error."""
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_by_signature(b"", "pdf")
        assert "empty" in str(exc_info.value).lower()


class TestValidateFileUpload:
    """Tests for complete file upload validation."""

    def test_valid_pdf_upload(self):
        """Test valid PDF upload."""
        filename = "document.pdf"
        content = b"%PDF-1.4\n" + b"x" * 1000
        file_type, size = validate_file_upload(filename, content)

        assert file_type == "pdf"
        assert size == len(content)

    def test_valid_docx_upload(self):
        """Test valid DOCX upload."""
        filename = "document.docx"
        content = b"PK\x03\x04" + b"x" * 1000
        file_type, size = validate_file_upload(filename, content)

        assert file_type == "docx"
        assert size == len(content)

    def test_valid_txt_upload(self):
        """Test valid TXT upload."""
        filename = "document.txt"
        content = "Hello, world!".encode("utf-8")
        file_type, size = validate_file_upload(filename, content)

        assert file_type == "txt"
        assert size == len(content)

    def test_unsupported_file_type(self):
        """Test unsupported file type rejected."""
        with pytest.raises(FileValidationError):
            validate_file_upload("image.jpg", b"fake image data")

    def test_file_too_large(self):
        """Test file size limit enforcement."""
        filename = "large.pdf"
        content = b"%PDF-1.4\n" + b"x" * (51 * 1024 * 1024)  # 51 MB
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_upload(filename, content)
        assert "exceeds" in str(exc_info.value).lower()

    def test_empty_file_rejected(self):
        """Test empty file rejected."""
        with pytest.raises(FileValidationError) as exc_info:
            validate_file_upload("empty.pdf", b"")
        assert "empty" in str(exc_info.value).lower()

    def test_wrong_signature_for_claimed_type(self):
        """Test signature mismatch with claimed type."""
        with pytest.raises(FileValidationError):
            validate_file_upload("fake.pdf", b"Not a PDF file")

    def test_allowed_types_filter(self):
        """Test allowed_types parameter."""
        filename = "document.txt"
        content = "Hello".encode("utf-8")

        # Should fail when txt not in allowed
        with pytest.raises(FileValidationError):
            validate_file_upload(filename, content, allowed_types=["pdf", "docx"])

        # Should pass when txt in allowed
        file_type, size = validate_file_upload(
            filename, content, allowed_types=["txt", "pdf"]
        )
        assert file_type == "txt"
