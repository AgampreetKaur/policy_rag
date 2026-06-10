"""
main.py — FastAPI REST API backend for PolicyLens
Run with: uvicorn main:app --reload
"""
from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

from core.document_processor import DocumentProcessor
from core.knowledge_base import PolicyKnowledgeBase
from core.rag_engine import RAGEngine
from agents.orchestrator import PolicyAnalysisOrchestrator
from utils.comparison_engine import PolicyComparisonEngine
from utils.timeline_extractor import TimelineExtractor
from evaluation.ragas_evaluator import RAGASEvaluator

# ── App Init ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="PolicyLens API",
    description="Agentic RAG System for Government Policy Analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singleton Services ────────────────────────────────────────────────────
processor = DocumentProcessor()
kb = PolicyKnowledgeBase()
rag = RAGEngine(kb)
orchestrator = PolicyAnalysisOrchestrator(rag, kb)
comparison_engine = PolicyComparisonEngine(rag, kb)
timeline_extractor = TimelineExtractor(rag)
evaluator = RAGASEvaluator(rag, kb)


# ── Request Models ────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str
    doc_ids: Optional[List[str]] = None
    n_results: int = 5


class AnalysisRequest(BaseModel):
    doc_id: str
    stakeholder: Optional[str] = None


class CompareRequest(BaseModel):
    doc_id_a: str
    doc_id_b: str


class StakeholderRequest(BaseModel):
    doc_id: str
    stakeholder: str


# ── Routes ────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "app": "PolicyLens",
        "version": "1.0.0",
        "docs": "/docs",
        "documents_indexed": kb.document_count,
    }


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and index a policy PDF."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    file_bytes = await file.read()
    try:
        doc = processor.process_bytes(file_bytes, file.filename)
        kb.add_document(doc)
        return {
            "doc_id": doc.doc_id,
            "filename": doc.filename,
            "title": doc.title,
            "pages": doc.pages,
            "chunks": len(doc.chunks),
        }
    except Exception as e:
        raise HTTPException(500, f"Processing failed: {str(e)}")


@app.get("/documents")
def list_documents():
    """List all indexed documents."""
    return {"documents": kb.documents, "total": kb.document_count}


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    """Remove a document from the knowledge base."""
    kb.remove_document(doc_id)
    return {"deleted": doc_id}


@app.post("/query")
def query_policy(request: QueryRequest):
    """RAG query against policy documents."""
    result = rag.query(
        request.question,
        doc_ids=request.doc_ids,
        n_results=request.n_results
    )
    return {
        "answer": result["answer"],
        "sources": [
            {"filename": s["filename"], "score": s["score"], "excerpt": s["text"][:200]}
            for s in result["sources"]
        ]
    }


@app.post("/analyze")
def analyze_document(request: AnalysisRequest):
    """Run full multi-agent analysis pipeline."""
    if not kb.get_doc_info(request.doc_id):
        raise HTTPException(404, f"Document {request.doc_id} not found")

    report = orchestrator.run_full_analysis(request.doc_id, request.stakeholder)
    return report


@app.post("/analyze/policy")
def run_policy_agent(request: AnalysisRequest):
    return orchestrator.policy_agent.analyze(request.doc_id)


@app.post("/analyze/impact")
def run_impact_agent(request: AnalysisRequest):
    return orchestrator.impact_agent.analyze(request.doc_id)


@app.post("/analyze/risk")
def run_risk_agent(request: AnalysisRequest):
    return orchestrator.risk_agent.analyze(request.doc_id)


@app.post("/analyze/stakeholder")
def run_stakeholder_agent(request: StakeholderRequest):
    return orchestrator.citizen_agent.simulate_stakeholder_impact(
        request.doc_id, request.stakeholder
    )


@app.post("/compare")
def compare_policies(request: CompareRequest):
    """Compare two policy documents."""
    if not kb.get_doc_info(request.doc_id_a):
        raise HTTPException(404, f"Document A not found: {request.doc_id_a}")
    if not kb.get_doc_info(request.doc_id_b):
        raise HTTPException(404, f"Document B not found: {request.doc_id_b}")

    result = comparison_engine.compare(request.doc_id_a, request.doc_id_b)
    return result


@app.post("/timeline/{doc_id}")
def extract_timeline(doc_id: str):
    """Extract policy timeline events."""
    if not kb.get_doc_info(doc_id):
        raise HTTPException(404, f"Document not found: {doc_id}")
    return timeline_extractor.extract(doc_id)


@app.post("/evaluate/{doc_id}")
def evaluate_rag(doc_id: str, questions: Optional[List[str]] = None):
    """Run RAGAS evaluation on a document."""
    if not kb.get_doc_info(doc_id):
        raise HTTPException(404, f"Document not found: {doc_id}")
    return evaluator.evaluate(doc_id, questions=questions)


@app.get("/health")
def health():
    return {"status": "healthy", "documents": kb.document_count}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
