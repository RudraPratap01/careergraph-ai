"""
Text extraction utility for resumes (PDF, DOCX, TXT).

Phase 3: Resume Intelligence
Handles secure file validation, size limits, and clean text extraction.
"""

import io
import re
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from pypdf import PdfReader
from docx import Document

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def extract_text_from_pdf(content: bytes) -> str:
    """Extracts text content from PDF bytes using pypdf."""
    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The uploaded PDF is password-protected and cannot be parsed.",
                )

        text_parts = []
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        full_text = "\n".join(text_parts).strip()
        if not full_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The PDF contains no selectable text (it may be a scanned image or empty).",
            )
        return full_text
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse PDF file: {str(e)}",
        )


def extract_text_from_docx(content: bytes) -> str:
    """Extracts text content from DOCX bytes using python-docx."""
    try:
        doc = Document(io.BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

        # Also extract text from any tables in the document
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        paragraphs.append(cell.text.strip())

        full_text = "\n".join(paragraphs).strip()
        if not full_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The DOCX document is empty or contains no readable text.",
            )
        return full_text
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse DOCX file: {str(e)}",
        )


def extract_text_from_txt(content: bytes) -> str:
    """Extracts text content from plain text bytes with encoding fallbacks."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            text = content.decode(encoding).strip()
            if text:
                return text
        except UnicodeDecodeError:
            continue

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unable to decode text file. Please ensure it is saved with UTF-8 encoding.",
    )


def clean_extracted_text(text: str) -> str:
    """Normalizes whitespace and removes unprintable control characters."""
    # Replace non-breaking spaces and tabs with normal space
    text = text.replace("\xa0", " ").replace("\t", " ")
    # Replace carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove control characters except newline and space
    text = re.sub(r"[^\x20-\x7E\n\t]", " ", text)
    # Collapse repeated horizontal spaces
    text = re.sub(r"[ ]{2,}", " ", text)
    return text.strip()


async def validate_and_extract_text(file: UploadFile) -> Tuple[str, str, int]:
    """
    Validates uploaded resume file and extracts clean text.

    Returns:
        (extracted_text, file_type, file_size_bytes)
    """
    filename = file.filename or "resume.pdf"
    extension = "." + filename.split(".")[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{extension}'. Allowed formats: .pdf, .docx, .txt",
        )

    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the 10 MB limit ({file_size / (1024 * 1024):.2f} MB).",
        )

    # Extract text based on file type
    if extension == ".pdf":
        raw_text = extract_text_from_pdf(content)
        file_type = "pdf"
    elif extension == ".docx":
        raw_text = extract_text_from_docx(content)
        file_type = "docx"
    else:
        raw_text = extract_text_from_txt(content)
        file_type = "txt"

    cleaned_text = clean_extracted_text(raw_text)
    if len(cleaned_text) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The resume contains too little readable text to extract meaningful skills.",
        )

    return cleaned_text, file_type, file_size
