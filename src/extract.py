"""Extraction stage: turn a source PDF into a structured DocRecord."""

from .schema import DocRecord


def extract(pdf_path: str) -> DocRecord:
    """Extract a structured record from a single source PDF.

    Will use pdfplumber to read the PDF text and an LLM (via instructor)
    to populate a DocRecord with typed facts and their supporting quotes.

    Not implemented yet.
    """
    raise NotImplementedError
