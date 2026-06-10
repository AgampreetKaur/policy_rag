"""
tests/test_rag.py — Unit tests for core RAG pipeline
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import MagicMock, patch


class TestDocumentProcessor:
    def test_infer_title(self):
        from core.document_processor import DocumentProcessor
        proc = DocumentProcessor()
        assert proc._infer_title("national_education_policy.pdf") == "National Education Policy"
        assert proc._infer_title("ev-subsidy-2025.pdf") == "Ev Subsidy 2025"

    def test_clean_text(self):
        from core.document_processor import PDFExtractor
        extractor = PDFExtractor()
        raw = "Hello\n\n\n\nWorld   extra spaces\nPage 3 of 10"
        cleaned = extractor._clean_text(raw)
        assert "Page 3 of 10" not in cleaned
        assert "   " not in cleaned

    def test_chunk_creates_metadata(self):
        from core.document_processor import PolicyChunker
        chunker = PolicyChunker(chunk_size=100, overlap=20)
        text = "This is a test policy document. " * 20
        chunks = chunker.chunk(text, "doc_001", "test.pdf")
        assert len(chunks) > 0
        for chunk in chunks:
            assert "doc_id" in chunk
            assert "text" in chunk
            assert chunk["doc_id"] == "doc_001"
            assert chunk["filename"] == "test.pdf"


class TestKnowledgeBase:
    def test_empty_on_init(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
        from core.knowledge_base import PolicyKnowledgeBase
        kb = PolicyKnowledgeBase()
        assert kb.is_empty()
        assert kb.document_count == 0

    def test_add_and_query(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
        from core.knowledge_base import PolicyKnowledgeBase
        from core.document_processor import PolicyDocument

        kb = PolicyKnowledgeBase()
        doc = PolicyDocument(
            doc_id="test_001",
            filename="test.pdf",
            title="Test Policy",
            raw_text="The subsidy amount is 50000 rupees for eligible farmers.",
            pages=1,
            chunks=[{
                "chunk_id": "test_001_chunk_0000",
                "doc_id": "test_001",
                "filename": "test.pdf",
                "text": "The subsidy amount is 50000 rupees for eligible farmers.",
                "chunk_index": 0,
                "total_chunks": 1,
            }]
        )
        kb.add_document(doc)
        assert kb.document_count == 1
        results = kb.query("What is the subsidy amount?", n_results=1)
        assert len(results) > 0
        assert "50000" in results[0]["text"]


class TestRAGEngine:
    def test_query_returns_dict(self):
        mock_kb = MagicMock()
        mock_kb.query.return_value = [{
            "text": "The policy allocates ₹10,000 crore.",
            "filename": "budget.pdf",
            "doc_id": "doc_001",
            "chunk_index": 0,
            "score": 0.92,
        }]

        with patch("core.rag_engine.genai") as mock_genai:
            mock_response = MagicMock()
            mock_response.text = "The budget is ₹10,000 crore."
            mock_genai.GenerativeModel.return_value.generate_content.return_value = mock_response

            from core.rag_engine import RAGEngine
            engine = RAGEngine(mock_kb)
            result = engine.query("What is the budget?")

        assert "answer" in result
        assert "sources" in result
        assert "context_used" in result

    def test_empty_kb_returns_graceful_message(self):
        mock_kb = MagicMock()
        mock_kb.query.return_value = []

        with patch("core.rag_engine.genai"):
            from core.rag_engine import RAGEngine
            engine = RAGEngine(mock_kb)
            result = engine.query("What is the budget?")

        assert "couldn't find" in result["answer"].lower() or "upload" in result["answer"].lower()
        assert result["sources"] == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
