"""
agents/policy_agent.py — Summarize, extract objectives, identify stakeholders
"""
from __future__ import annotations

import json
from typing import Optional

from core.rag_engine import RAGEngine
from core.knowledge_base import PolicyKnowledgeBase


class PolicyUnderstandingAgent:
    """
    Agent 1: Policy Understanding
    - Summarizes the policy
    - Extracts objectives and key provisions
    - Identifies all stakeholders mentioned
    """

    def __init__(self, rag_engine: RAGEngine, kb: PolicyKnowledgeBase):
        self.rag = rag_engine
        self.kb = kb

    def analyze(self, doc_id: str) -> dict:
        """Full policy understanding analysis."""
        doc_info = self.kb.get_doc_info(doc_id)
        if not doc_info:
            return {"error": f"Document {doc_id} not found in knowledge base"}

        print(f"[PolicyAgent] Analyzing '{doc_info['title']}'...")

        summary = self._generate_summary(doc_id)
        objectives = self._extract_objectives(doc_id)
        stakeholders = self._identify_stakeholders(doc_id)
        key_provisions = self._extract_key_provisions(doc_id)
        eligibility = self._extract_eligibility(doc_id)

        return {
            "agent": "Policy Understanding Agent",
            "doc_id": doc_id,
            "policy_name": doc_info["title"],
            "summary": summary,
            "objectives": objectives,
            "stakeholders": stakeholders,
            "key_provisions": key_provisions,
            "eligibility": eligibility,
        }

    def _generate_summary(self, doc_id: str) -> str:
        result = self.rag.query(
            "Provide a comprehensive executive summary of this policy. "
            "Cover: purpose, scope, key measures, target beneficiaries, and implementation timeline.",
            doc_ids=[doc_id],
            n_results=7,
            system_prompt="You are a senior policy analyst. Write a clear, structured executive summary."
        )
        return result["answer"]

    def _extract_objectives(self, doc_id: str) -> list:
        prompt = """From the policy document, extract ALL stated objectives and goals.
Return a JSON array of strings, each being one objective.
Example: ["Increase EV adoption by 30% by 2030", "Reduce carbon emissions", ...]
Extract from the document context provided."""

        result = self.rag.query(prompt, doc_ids=[doc_id], n_results=5)
        try:
            text = result["answer"]
            # Find JSON array in response
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except Exception:
            pass
        # Fallback: split by newlines
        lines = [l.strip("•- ").strip() for l in result["answer"].split("\n") if l.strip()]
        return [l for l in lines if len(l) > 10][:8]

    def _identify_stakeholders(self, doc_id: str) -> list:
        prompt = """Who are all the stakeholders mentioned or affected by this policy?
Return a JSON array of objects: [{"name": "...", "role": "beneficiary/implementer/regulator", "description": "..."}]"""

        result = self.rag.query(prompt, doc_ids=[doc_id], n_results=5)
        try:
            text = result["answer"]
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except Exception:
            pass
        return [{"name": "General Public", "role": "beneficiary", "description": "Citizens affected by the policy"}]

    def _extract_key_provisions(self, doc_id: str) -> list:
        result = self.rag.query(
            "What are the key provisions, schemes, subsidies, or benefits mentioned in this policy? List each one.",
            doc_ids=[doc_id],
            n_results=6
        )
        lines = [l.strip("•-123456789. ").strip() for l in result["answer"].split("\n") if l.strip()]
        return [l for l in lines if len(l) > 15][:10]

    def _extract_eligibility(self, doc_id: str) -> str:
        result = self.rag.query(
            "What are the eligibility criteria? Who qualifies and what are the conditions?",
            doc_ids=[doc_id],
            n_results=5
        )
        return result["answer"]
