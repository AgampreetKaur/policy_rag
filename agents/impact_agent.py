"""
agents/impact_agent.py — Economic, social, and administrative impact analysis
"""
from __future__ import annotations

import json

from core.rag_engine import RAGEngine
from core.knowledge_base import PolicyKnowledgeBase


class ImpactAnalysisAgent:
    """
    Agent 2: Impact Analysis
    - Economic impact (GDP, employment, costs, subsidies)
    - Social impact (equity, inclusion, welfare)
    - Administrative impact (implementation burden, governance)
    - Environmental impact (if applicable)
    """

    def __init__(self, rag_engine: RAGEngine, kb: PolicyKnowledgeBase):
        self.rag = rag_engine
        self.kb = kb

    def analyze(self, doc_id: str) -> dict:
        doc_info = self.kb.get_doc_info(doc_id)
        print(f"[ImpactAgent] Analyzing impact for '{doc_info['title']}'...")

        economic = self._economic_impact(doc_id)
        social = self._social_impact(doc_id)
        administrative = self._administrative_impact(doc_id)
        environmental = self._environmental_impact(doc_id)
        overall_score = self._compute_impact_score(economic, social, administrative)

        return {
            "agent": "Impact Analysis Agent",
            "doc_id": doc_id,
            "policy_name": doc_info["title"],
            "economic_impact": economic,
            "social_impact": social,
            "administrative_impact": administrative,
            "environmental_impact": environmental,
            "overall_impact_score": overall_score,
        }

    def _economic_impact(self, doc_id: str) -> dict:
        pos_result = self.rag.query(
            "What are the positive economic impacts? Include: cost savings, job creation, "
            "GDP contribution, subsidies, investment attracted.",
            doc_ids=[doc_id], n_results=5
        )
        neg_result = self.rag.query(
            "What are the negative economic impacts or costs? Include: budget expenditure, "
            "compliance costs, market distortions, fiscal burden.",
            doc_ids=[doc_id], n_results=5
        )
        budget_result = self.rag.query(
            "What is the budget allocation, funding amount, or financial outlay mentioned?",
            doc_ids=[doc_id], n_results=3
        )

        return {
            "positive": self._parse_bullet_list(pos_result["answer"]),
            "negative": self._parse_bullet_list(neg_result["answer"]),
            "budget_details": budget_result["answer"],
            "raw_positive": pos_result["answer"],
            "raw_negative": neg_result["answer"],
        }

    def _social_impact(self, doc_id: str) -> dict:
        pos_result = self.rag.query(
            "What are the positive social impacts? Include: education access, healthcare, "
            "poverty reduction, women empowerment, rural development, social equity.",
            doc_ids=[doc_id], n_results=5
        )
        neg_result = self.rag.query(
            "What are potential negative social impacts? Include: displacement, inequality, "
            "exclusion of vulnerable groups, unintended consequences.",
            doc_ids=[doc_id], n_results=5
        )
        return {
            "positive": self._parse_bullet_list(pos_result["answer"]),
            "negative": self._parse_bullet_list(neg_result["answer"]),
            "raw_positive": pos_result["answer"],
            "raw_negative": neg_result["answer"],
        }

    def _administrative_impact(self, doc_id: str) -> dict:
        result = self.rag.query(
            "What are the administrative requirements, implementation challenges, "
            "institutional responsibilities, and governance structures described?",
            doc_ids=[doc_id], n_results=5
        )
        return {
            "details": result["answer"],
            "points": self._parse_bullet_list(result["answer"]),
        }

    def _environmental_impact(self, doc_id: str) -> dict:
        result = self.rag.query(
            "Are there any environmental impacts, sustainability goals, or climate-related "
            "provisions in this policy?",
            doc_ids=[doc_id], n_results=3
        )
        return {"details": result["answer"]}

    def _compute_impact_score(self, economic: dict, social: dict, admin: dict) -> dict:
        """Heuristic impact scoring based on number of positive vs negative points."""
        pos_count = len(economic.get("positive", [])) + len(social.get("positive", []))
        neg_count = len(economic.get("negative", [])) + len(social.get("negative", []))
        total = pos_count + neg_count or 1
        score = round((pos_count / total) * 10, 1)

        return {
            "score": score,
            "max": 10,
            "sentiment": "Positive" if score >= 6 else "Mixed" if score >= 4 else "Concerning",
            "positive_points": pos_count,
            "negative_points": neg_count,
        }

    def _parse_bullet_list(self, text: str) -> list:
        """Extract bullet points from LLM response."""
        lines = text.split("\n")
        points = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Remove bullet markers
            clean = line.lstrip("•-*–123456789. ").strip()
            if len(clean) > 15:
                points.append(clean)
        return points[:8]
