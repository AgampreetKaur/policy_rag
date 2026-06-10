"""
agents/risk_agent.py — Implementation, compliance, and budget risk identification
"""
from __future__ import annotations

import json
from typing import List

from core.rag_engine import RAGEngine
from core.knowledge_base import PolicyKnowledgeBase
from core.config import RISK_CATEGORIES


class RiskAssessmentAgent:
    """
    Agent 3: Risk Assessment
    - Implementation risks
    - Compliance risks
    - Budget/financial risks
    - Political risks
    - Social risks
    - Technical risks
    """

    def __init__(self, rag_engine: RAGEngine, kb: PolicyKnowledgeBase):
        self.rag = rag_engine
        self.kb = kb

    def analyze(self, doc_id: str) -> dict:
        doc_info = self.kb.get_doc_info(doc_id)
        print(f"[RiskAgent] Assessing risks for '{doc_info['title']}'...")

        risks = []
        for category in RISK_CATEGORIES:
            category_risks = self._assess_category(doc_id, category)
            risks.extend(category_risks)

        mitigation = self._suggest_mitigations(doc_id, risks)
        summary = self._risk_summary(risks)

        return {
            "agent": "Risk Assessment Agent",
            "doc_id": doc_id,
            "policy_name": doc_info["title"],
            "risks": risks,
            "mitigation_strategies": mitigation,
            "risk_summary": summary,
            "overall_risk_level": self._overall_level(risks),
        }

    def _assess_category(self, doc_id: str, category: str) -> List[dict]:
        prompts = {
            "Implementation": "What implementation challenges, infrastructure gaps, or execution risks exist? Consider capacity, timelines, and coordination.",
            "Compliance": "What compliance requirements, regulatory burdens, or legal risks does this policy create for beneficiaries or implementers?",
            "Budget": "What budget risks, cost overruns, funding shortfalls, or fiscal sustainability concerns are there?",
            "Political": "What political risks, stakeholder resistance, or governance challenges might affect this policy?",
            "Social": "What social risks, unintended consequences, or equity concerns could arise from this policy?",
            "Technical": "What technical risks, data infrastructure gaps, or digital divide issues could hinder this policy?",
        }

        result = self.rag.query(
            f"{prompts[category]} List specific risks as bullet points.",
            doc_ids=[doc_id],
            n_results=4
        )

        # Parse risks from response
        risks = []
        lines = result["answer"].split("\n")
        for line in lines:
            clean = line.strip().lstrip("•-*–123456789. ").strip()
            if len(clean) > 20:
                # Estimate severity based on keywords
                severity = self._estimate_severity(clean)
                risks.append({
                    "category": category,
                    "description": clean,
                    "severity": severity,
                    "likelihood": self._estimate_likelihood(clean),
                })
                if len(risks) >= 2:  # max 2 per category to keep it focused
                    break

        return risks

    def _estimate_severity(self, text: str) -> str:
        high_keywords = ["critical", "major", "severe", "significant", "fail", "collapse",
                        "unable", "shortage", "corruption", "fraud", "delay"]
        low_keywords = ["minor", "small", "limited", "manageable", "unlikely", "possible"]
        text_lower = text.lower()
        if any(kw in text_lower for kw in high_keywords):
            return "High"
        if any(kw in text_lower for kw in low_keywords):
            return "Low"
        return "Medium"

    def _estimate_likelihood(self, text: str) -> str:
        high_kw = ["likely", "common", "often", "typically", "historically", "past"]
        low_kw = ["unlikely", "rare", "exceptional", "unlikely"]
        text_lower = text.lower()
        if any(kw in text_lower for kw in high_kw):
            return "High"
        if any(kw in text_lower for kw in low_kw):
            return "Low"
        return "Medium"

    def _suggest_mitigations(self, doc_id: str, risks: List[dict]) -> List[str]:
        if not risks:
            return []
        top_risks = [r["description"] for r in risks[:5]]
        risk_text = "\n".join(f"- {r}" for r in top_risks)

        result = self.rag.query(
            f"Given these policy risks:\n{risk_text}\n\nWhat mitigation strategies does the policy suggest, "
            "or what best practices would address these risks?",
            doc_ids=[doc_id], n_results=4
        )
        lines = result["answer"].split("\n")
        return [l.strip().lstrip("•-*–123456789. ").strip() for l in lines
                if len(l.strip()) > 20][:6]

    def _risk_summary(self, risks: List[dict]) -> dict:
        from collections import Counter
        severities = Counter(r["severity"] for r in risks)
        categories = Counter(r["category"] for r in risks)
        return {
            "total_risks": len(risks),
            "by_severity": dict(severities),
            "by_category": dict(categories),
            "high_risk_count": severities.get("High", 0),
        }

    def _overall_level(self, risks: List[dict]) -> str:
        high_count = sum(1 for r in risks if r["severity"] == "High")
        if high_count >= 3:
            return "High"
        if high_count >= 1:
            return "Medium"
        return "Low"
