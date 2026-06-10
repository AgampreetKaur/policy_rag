"""
agents/citizen_agent.py — Citizen Q&A, eligibility checks, stakeholder impact simulation
"""
from __future__ import annotations

from core.rag_engine import RAGEngine
from core.knowledge_base import PolicyKnowledgeBase
from core.config import STAKEHOLDER_PROFILES


class CitizenGuidanceAgent:
    """
    Agent 4: Citizen Guidance
    - Eligibility checks
    - Application guidance
    - Stakeholder-specific impact simulation
    - Plain-language explanations
    """

    def __init__(self, rag_engine: RAGEngine, kb: PolicyKnowledgeBase):
        self.rag = rag_engine
        self.kb = kb

    def answer_citizen_query(self, question: str, doc_ids: list, stakeholder: str = None) -> dict:
        """Answer a citizen's specific question about the policy."""
        context_prefix = ""
        if stakeholder:
            profile = STAKEHOLDER_PROFILES.get(stakeholder, {})
            context_prefix = (
                f"The user is a {stakeholder}. They care about: {profile.get('focus', '')}. "
                f"Their concerns include: {profile.get('concerns', '')}. "
            )

        system_prompt = f"""You are a helpful policy advisor speaking directly to a citizen.
{context_prefix}
Explain in simple, clear language. Use plain English, avoid jargon.
If eligibility criteria exist, state them clearly as a checklist.
If there are deadlines, highlight them.
Always be practical and actionable."""

        result = self.rag.query(
            question,
            doc_ids=doc_ids,
            n_results=5,
            system_prompt=system_prompt
        )
        return result

    def simulate_stakeholder_impact(self, doc_id: str, stakeholder: str) -> dict:
        """
        Full stakeholder impact simulation.
        Returns benefits, risks, action items, and impact score for a specific stakeholder type.
        """
        profile = STAKEHOLDER_PROFILES.get(stakeholder)
        if not profile:
            return {"error": f"Unknown stakeholder type: {stakeholder}"}

        doc_info = self.kb.get_doc_info(doc_id)
        print(f"[CitizenAgent] Simulating impact for {stakeholder} on '{doc_info['title']}'...")

        benefits = self._get_benefits(doc_id, stakeholder, profile)
        risks = self._get_risks(doc_id, stakeholder, profile)
        actions = self._get_required_actions(doc_id, stakeholder)
        eligibility = self._check_eligibility(doc_id, stakeholder, profile)
        score = self._compute_impact_score(benefits, risks)

        return {
            "stakeholder": stakeholder,
            "icon": profile["icon"],
            "policy_name": doc_info["title"],
            "impact_score": score,
            "benefits": benefits,
            "risks": risks,
            "required_actions": actions,
            "eligibility_summary": eligibility,
            "verdict": self._verdict(score),
        }

    def _get_benefits(self, doc_id: str, stakeholder: str, profile: dict) -> list:
        result = self.rag.query(
            f"What specific benefits, subsidies, grants, or advantages does this policy offer to a {stakeholder}? "
            f"Focus on: {profile['focus']}. Be specific with amounts or percentages if mentioned.",
            doc_ids=[doc_id], n_results=5
        )
        return self._parse_list(result["answer"])

    def _get_risks(self, doc_id: str, stakeholder: str, profile: dict) -> list:
        result = self.rag.query(
            f"What risks, challenges, compliance requirements, or additional burdens does this policy create for a {stakeholder}? "
            f"Their concerns include: {profile['concerns']}.",
            doc_ids=[doc_id], n_results=4
        )
        return self._parse_list(result["answer"])

    def _get_required_actions(self, doc_id: str, stakeholder: str) -> list:
        result = self.rag.query(
            f"What actions does a {stakeholder} need to take to benefit from this policy? "
            "What documents are required? What is the application process? What are the deadlines?",
            doc_ids=[doc_id], n_results=5
        )
        return self._parse_list(result["answer"])

    def _check_eligibility(self, doc_id: str, stakeholder: str, profile: dict) -> str:
        result = self.rag.query(
            f"Is a {stakeholder} eligible for the benefits in this policy? "
            f"What are the specific eligibility conditions for someone focused on {profile['focus']}?",
            doc_ids=[doc_id], n_results=4,
            system_prompt=f"Assess eligibility for a {stakeholder} clearly. Start with YES/NO/LIKELY/DEPENDS."
        )
        return result["answer"]

    def _compute_impact_score(self, benefits: list, risks: list) -> float:
        """Score from 0-10 based on benefit/risk ratio."""
        b = len(benefits)
        r = len(risks)
        if b + r == 0:
            return 5.0
        base = (b / (b + r)) * 10
        # Bonus for many benefits
        if b >= 5:
            base = min(10, base + 0.5)
        return round(base, 1)

    def _verdict(self, score: float) -> str:
        if score >= 7.5:
            return "Highly Beneficial"
        if score >= 5.5:
            return "Moderately Beneficial"
        if score >= 4.0:
            return "Mixed Impact"
        return "Potentially Challenging"

    def _parse_list(self, text: str) -> list:
        lines = text.split("\n")
        items = []
        for line in lines:
            clean = line.strip().lstrip("•-*–123456789. ").strip()
            if len(clean) > 15:
                items.append(clean)
        return items[:6]
