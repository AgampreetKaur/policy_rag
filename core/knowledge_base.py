"""
core/knowledge_base.py — ChromaDB vector store for policy documents
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from core.config import CHROMA_DIR, EMBEDDING_MODEL
from core.document_processor import PolicyDocument


class PolicyKnowledgeBase:
    """
    Manages the ChromaDB vector store for policy documents.
    Supports multi-document storage, retrieval, and metadata filtering.
    """

    COLLECTION_NAME = "policy_documents"
    DOC_REGISTRY_FILE = Path(CHROMA_DIR) / "doc_registry.json"

    def __init__(self):
        Path(CHROMA_DIR).mkdir(parents=True, exist_ok=True)

        # Persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False)
        )

        # Sentence-transformer embeddings (local, no API key needed)
        print(f"[KnowledgeBase] Loading embedding model '{EMBEDDING_MODEL}'...")
        self.encoder = SentenceTransformer(EMBEDDING_MODEL)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        # In-memory doc registry (persisted to JSON)
        self._registry: dict = self._load_registry()

    # ── Indexing ──────────────────────────────────────────────────────────

    def add_document(self, doc: PolicyDocument) -> None:
        """Add a PolicyDocument to the knowledge base."""
        if doc.doc_id in self._registry:
            print(f"[KnowledgeBase] '{doc.filename}' already indexed, skipping.")
            return

        print(f"[KnowledgeBase] Indexing {len(doc.chunks)} chunks for '{doc.filename}'...")

        # Encode in batches
        batch_size = 64
        for i in range(0, len(doc.chunks), batch_size):
            batch = doc.chunks[i:i + batch_size]
            texts = [c["text"] for c in batch]
            embeddings = self.encoder.encode(texts, show_progress_bar=False).tolist()

            self.collection.add(
                ids=[c["chunk_id"] for c in batch],
                embeddings=embeddings,
                documents=texts,
                metadatas=[{
                    "doc_id": c["doc_id"],
                    "filename": c["filename"],
                    "chunk_index": c["chunk_index"],
                } for c in batch]
            )

        # Register document
        self._registry[doc.doc_id] = {
            "doc_id": doc.doc_id,
            "filename": doc.filename,
            "title": doc.title,
            "pages": doc.pages,
            "word_count": doc.word_count,
            "chunk_count": len(doc.chunks),
        }
        self._save_registry()
        print(f"[KnowledgeBase] ✓ Indexed '{doc.filename}'")

    def remove_document(self, doc_id: str) -> None:
        """Remove all chunks for a document."""
        results = self.collection.get(where={"doc_id": doc_id})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
        self._registry.pop(doc_id, None)
        self._save_registry()

    # ── Retrieval ─────────────────────────────────────────────────────────

    def query(
        self,
        query_text: str,
        n_results: int = 5,
        doc_ids: Optional[List[str]] = None,
    ) -> List[dict]:
        """
        Semantic search. Returns list of {text, filename, score, chunk_index}.
        Optionally filter to specific doc_ids.
        """
        query_embedding = self.encoder.encode([query_text]).tolist()

        where_clause = None
        if doc_ids and len(doc_ids) == 1:
            where_clause = {"doc_id": doc_ids[0]}
        elif doc_ids and len(doc_ids) > 1:
            where_clause = {"doc_id": {"$in": doc_ids}}

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(n_results, self.collection.count() or 1),
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )

        chunks = []
        for text, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            chunks.append({
                "text": text,
                "filename": meta.get("filename", ""),
                "doc_id": meta.get("doc_id", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "score": round(1 - dist, 4),  # cosine similarity
            })
        return chunks

    def get_full_text(self, doc_id: str) -> str:
        """Retrieve all chunks for a doc and reassemble text."""
        results = self.collection.get(
            where={"doc_id": doc_id},
            include=["documents", "metadatas"]
        )
        if not results["ids"]:
            return ""
        # Sort by chunk_index
        pairs = sorted(
            zip(results["metadatas"], results["documents"]),
            key=lambda x: x[0].get("chunk_index", 0)
        )
        return "\n\n".join(doc for _, doc in pairs)

    # ── Registry ──────────────────────────────────────────────────────────

    @property
    def documents(self) -> List[dict]:
        """List all indexed documents."""
        return list(self._registry.values())

    @property
    def document_count(self) -> int:
        return len(self._registry)

    def get_doc_info(self, doc_id: str) -> Optional[dict]:
        return self._registry.get(doc_id)

    def is_empty(self) -> bool:
        return self.collection.count() == 0

    def _load_registry(self) -> dict:
        if self.DOC_REGISTRY_FILE.exists():
            with open(self.DOC_REGISTRY_FILE) as f:
                return json.load(f)
        return {}

    def _save_registry(self) -> None:
        self.DOC_REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.DOC_REGISTRY_FILE, "w") as f:
            json.dump(self._registry, f, indent=2)
