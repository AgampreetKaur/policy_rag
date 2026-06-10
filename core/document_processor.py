"""
core/document_processor.py — PDF ingestion, text extraction, and chunking
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import pdfplumber
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter

from core.config import CHUNK_SIZE, CHUNK_OVERLAP


# ── Data Models ───────────────────────────────────────────────────────────

@dataclass
class PolicyDocument:
    """Represents a processed policy document."""
    doc_id: str
    filename: str
    title: str
    raw_text: str
    pages: int
    chunks: List[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def word_count(self) -> int:
        return len(self.raw_text.split())


# ── PDF Extraction ────────────────────────────────────────────────────────

class PDFExtractor:
    """Extracts text from PDFs using pdfplumber with PyPDF2 fallback."""

    def extract(self, pdf_path: str | Path) -> tuple[str, int]:
        """Returns (full_text, page_count)."""
        pdf_path = Path(pdf_path)
        text_parts = []
        page_count = 0

        # Primary: pdfplumber (handles tables and complex layouts better)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    # Also extract tables as structured text
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            cleaned_row = [cell or "" for cell in row]
                            page_text += "\n" + " | ".join(cleaned_row)
                    text_parts.append(page_text)
            full_text = "\n\n".join(text_parts)
            if len(full_text.strip()) > 100:
                return self._clean_text(full_text), page_count
        except Exception as e:
            print(f"[pdfplumber] failed: {e}, falling back to PyPDF2")

        # Fallback: PyPDF2
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                page_count = len(reader.pages)
                for page in reader.pages:
                    text_parts.append(page.extract_text() or "")
            return self._clean_text("\n\n".join(text_parts)), page_count
        except Exception as e:
            raise RuntimeError(f"Could not extract text from {pdf_path}: {e}")

    def _clean_text(self, text: str) -> str:
        """Remove excessive whitespace, headers/footers noise."""
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)
        text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
        return text.strip()


# ── Chunker ───────────────────────────────────────────────────────────────

class PolicyChunker:
    """Splits policy text into semantically meaningful chunks."""

    def __init__(self, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def chunk(self, text: str, doc_id: str, filename: str) -> List[dict]:
        """Returns list of chunk dicts with metadata."""
        raw_chunks = self.splitter.split_text(text)
        chunks = []
        for i, chunk_text in enumerate(raw_chunks):
            chunks.append({
                "chunk_id": f"{doc_id}_chunk_{i:04d}",
                "doc_id": doc_id,
                "filename": filename,
                "text": chunk_text,
                "chunk_index": i,
                "total_chunks": len(raw_chunks),
            })
        return chunks


# ── Main Processor ────────────────────────────────────────────────────────

class DocumentProcessor:
    """End-to-end pipeline: PDF → PolicyDocument with chunks."""

    def __init__(self):
        self.extractor = PDFExtractor()
        self.chunker = PolicyChunker()

    def process(self, pdf_path: str | Path, title: Optional[str] = None) -> PolicyDocument:
        """Process a PDF file into a PolicyDocument."""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Generate stable doc_id from file content hash
        file_hash = hashlib.md5(pdf_path.read_bytes()).hexdigest()[:12]
        doc_id = f"doc_{file_hash}"

        filename = pdf_path.name
        title = title or self._infer_title(filename)

        print(f"[DocumentProcessor] Extracting text from '{filename}'...")
        raw_text, page_count = self.extractor.extract(pdf_path)

        print(f"[DocumentProcessor] Chunking {len(raw_text)} chars across {page_count} pages...")
        chunks = self.chunker.chunk(raw_text, doc_id, filename)

        doc = PolicyDocument(
            doc_id=doc_id,
            filename=filename,
            title=title,
            raw_text=raw_text,
            pages=page_count,
            chunks=chunks,
            metadata={
                "source": str(pdf_path),
                "pages": page_count,
                "word_count": len(raw_text.split()),
                "chunk_count": len(chunks),
            }
        )
        print(f"[DocumentProcessor] ✓ '{filename}' → {len(chunks)} chunks, {page_count} pages")
        return doc

    def _infer_title(self, filename: str) -> str:
        """Convert filename to readable title."""
        name = Path(filename).stem
        name = re.sub(r'[_\-]+', ' ', name)
        return name.title()

    def process_bytes(self, file_bytes: bytes, filename: str, title: Optional[str] = None) -> PolicyDocument:
        """Process PDF from bytes (for Streamlit upload)."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)
        try:
            return self.process(tmp_path, title or filename)
        finally:
            tmp_path.unlink(missing_ok=True)
