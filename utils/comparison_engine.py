"""
utils/comparison_engine.py — GitHub-style policy diff and comparison
"""
from __future__ import annotations

import difflib
from typing import List

from core.rag_engine import RAGEngine
from core.knowledge_base import PolicyKnowledgeBase


class PolicyComparisonEngine:
    """
    Compare two policy documents and generate:
    - Semantic diff (what changed in objectives/provisions)
    - Side-by-side stakeholder impact comparison
    - Key additions and removals
    """

    def __init__(self, rag_engine: RAGEngine, kb: PolicyKnowledgeBase):
        self.rag = rag_engine
        self.kb = kb

    def compare(self, doc_id_a: str, doc_id_b: str) -> dict:
        """Full comparison between two policy documents."""
        doc_a = self.kb.get_doc_info(doc_id_a)
        doc_b = self.kb.get_doc_info(doc_id_b)

        if not doc_a or not doc_b:
            return {"error": "One or both documents not found"}

        print(f"[ComparisonEngine] Comparing '{doc_a['title']}' vs '{doc_b['title']}'...")

        objectives_diff = self._compare_objectives(doc_id_a, doc_id_b, doc_a, doc_b)
        provisions_diff = self._compare_provisions(doc_id_a, doc_id_b, doc_a, doc_b)
        stakeholder_diff = self._compare_stakeholder_impact(doc_id_a, doc_id_b, doc_a, doc_b)
        budget_diff = self._compare_budget(doc_id_a, doc_id_b, doc_a, doc_b)
        text_diff = self._text_diff(doc_id_a, doc_id_b)

        return {
            "policy_a": {"doc_id": doc_id_a, "title": doc_a["title"]},
            "policy_b": {"doc_id": doc_id_b, "title": doc_b["title"]},
            "objectives_diff": objectives_diff,
            "provisions_diff": provisions_diff,
            "stakeholder_diff": stakeholder_diff,
            "budget_diff": budget_diff,
            "text_diff_sample": text_diff,
            "ai_summary": self._ai_comparison_summary(doc_id_a, doc_id_b, doc_a, doc_b),
        }

    def _compare_objectives(self, id_a, id_b, doc_a, doc_b) -> dict:
        prompt_a = f"List ALL objectives and goals of this policy as a numbered list. Be concise."
        prompt_b = prompt_a

        res_a = self.rag.query(prompt_a, doc_ids=[id_a], n_results=5)
        res_b = self.rag.query(prompt_b, doc_ids=[id_b], n_results=5)

        lines_a = self._extract_lines(res_a["answer"])
        lines_b = self._extract_lines(res_b["answer"])

        added = [l for l in lines_b if not any(self._similar(l, la) for la in lines_a)]
        removed = [l for l in lines_a if not any(self._similar(l, lb) for lb in lines_b)]
        retained = [l for l in lines_a if any(self._similar(l, lb) for lb in lines_b)]

        return {
            "policy_a_objectives": lines_a,
            "policy_b_objectives": lines_b,
            "added": added,
            "removed": removed,
            "retained": retained,
        }

    def _compare_provisions(self, id_a, id_b, doc_a, doc_b) -> dict:
        res_a = self.rag.query(
            "List all subsidies, schemes, benefits, and financial provisions with amounts.",
            doc_ids=[id_a], n_results=6
        )
        res_b = self.rag.query(
            "List all subsidies, schemes, benefits, and financial provisions with amounts.",
            doc_ids=[id_b], n_results=6
        )
        return {
            "policy_a": res_a["answer"],
            "policy_b": res_b["answer"],
            "lines_a": self._extract_lines(res_a["answer"]),
            "lines_b": self._extract_lines(res_b["answer"]),
        }

    def _compare_stakeholder_impact(self, id_a, id_b, doc_a, doc_b) -> dict:
        result = self.rag.query(
            f"Compare how these two policy documents differ in their impact on citizens, businesses, and government agencies.",
            doc_ids=[id_a, id_b],
            n_results=6
        )
        return {"summary": result["answer"]}

    def _compare_budget(self, id_a, id_b, doc_a, doc_b) -> dict:
        res_a = self.rag.query("What is the total budget, financial outlay, or funding allocated?", doc_ids=[id_a], n_results=3)
        res_b = self.rag.query("What is the total budget, financial outlay, or funding allocated?", doc_ids=[id_b], n_results=3)
        return {
            "policy_a_budget": res_a["answer"],
            "policy_b_budget": res_b["answer"],
        }

    def _ai_comparison_summary(self, id_a, id_b, doc_a, doc_b) -> str:
        result = self.rag.query(
            f"Provide a detailed comparison between '{doc_a['title']}' and '{doc_b['title']}'. "
            "Cover: key differences in approach, beneficiaries, funding, scope, and implementation. "
            "What are the major improvements or regressions between the two?",
            doc_ids=[id_a, id_b],
            n_results=8
        )
        return result["answer"]

    def _text_diff(self, id_a: str, id_b: str) -> list:
        """Character-level text diff on first 3000 chars of each doc."""
        text_a = self.kb.get_full_text(id_a)[:3000]
        text_b = self.kb.get_full_text(id_b)[:3000]

        diff = list(difflib.unified_diff(
            text_a.splitlines(),
            text_b.splitlines(),
            lineterm="",
            n=2
        ))
        return diff[:50]  # Return first 50 diff lines

    def _extract_lines(self, text: str) -> List[str]:
        lines = []
        for line in text.split("\n"):
            clean = line.strip().lstrip("•-*–123456789. ").strip()
            if len(clean) > 10:
                lines.append(clean)
        return lines[:10]

    def _similar(self, a: str, b: str, threshold: float = 0.5) -> bool:
        """Check if two strings are semantically similar using sequence matching."""
        ratio = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
        return ratio >= threshold
