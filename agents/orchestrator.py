"""
agents/orchestrator.py — LangGraph multi-agent orchestration pipeline
"""
from __future__ import annotations

import json
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END

from core.rag_engine import RAGEngine
from core.knowledge_base import PolicyKnowledgeBase
from agents.policy_agent import PolicyUnderstandingAgent
from agents.impact_agent import ImpactAnalysisAgent
from agents.risk_agent import RiskAssessmentAgent
from agents.citizen_agent import CitizenGuidanceAgent


# ── State Schema ──────────────────────────────────────────────────────────

class AnalysisState(TypedDict):
    doc_id: str
    stakeholder: Optional[str]
    policy_analysis: Optional[dict]
    impact_analysis: Optional[dict]
    risk_analysis: Optional[dict]
    stakeholder_analysis: Optional[dict]
    final_report: Optional[dict]
    errors: List[str]


# ── Orchestrator ──────────────────────────────────────────────────────────

class PolicyAnalysisOrchestrator:
    """
    LangGraph-based multi-agent orchestrator.
    Runs 3-4 agents in sequence and aggregates a final report.
    """

    def __init__(self, rag_engine: RAGEngine, kb: PolicyKnowledgeBase):
        self.rag = rag_engine
        self.kb = kb

        # Instantiate agents
        self.policy_agent = PolicyUnderstandingAgent(rag_engine, kb)
        self.impact_agent = ImpactAnalysisAgent(rag_engine, kb)
        self.risk_agent = RiskAssessmentAgent(rag_engine, kb)
        self.citizen_agent = CitizenGuidanceAgent(rag_engine, kb)

        # Build graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(AnalysisState)

        # Add nodes
        graph.add_node("policy_node", self._run_policy_agent)
        graph.add_node("impact_node", self._run_impact_agent)
        graph.add_node("risk_node", self._run_risk_agent)
        graph.add_node("stakeholder_node", self._run_stakeholder_agent)
        graph.add_node("report_node", self._generate_final_report)

        # Define flow
        graph.set_entry_point("policy_node")
        graph.add_edge("policy_node", "impact_node")
        graph.add_edge("impact_node", "risk_node")
        graph.add_conditional_edges(
            "risk_node",
            self._should_run_stakeholder,
            {
                "stakeholder": "stakeholder_node",
                "report": "report_node",
            }
        )
        graph.add_edge("stakeholder_node", "report_node")
        graph.add_edge("report_node", END)

        return graph.compile()

    # ── Node Functions ────────────────────────────────────────────────────

    def _run_policy_agent(self, state: AnalysisState) -> AnalysisState:
        try:
            result = self.policy_agent.analyze(state["doc_id"])
            return {**state, "policy_analysis": result}
        except Exception as e:
            return {**state, "errors": state.get("errors", []) + [f"PolicyAgent: {e}"]}

    def _run_impact_agent(self, state: AnalysisState) -> AnalysisState:
        try:
            result = self.impact_agent.analyze(state["doc_id"])
            return {**state, "impact_analysis": result}
        except Exception as e:
            return {**state, "errors": state.get("errors", []) + [f"ImpactAgent: {e}"]}

    def _run_risk_agent(self, state: AnalysisState) -> AnalysisState:
        try:
            result = self.risk_agent.analyze(state["doc_id"])
            return {**state, "risk_analysis": result}
        except Exception as e:
            return {**state, "errors": state.get("errors", []) + [f"RiskAgent: {e}"]}

    def _run_stakeholder_agent(self, state: AnalysisState) -> AnalysisState:
        try:
            stakeholder = state.get("stakeholder", "Student")
            result = self.citizen_agent.simulate_stakeholder_impact(state["doc_id"], stakeholder)
            return {**state, "stakeholder_analysis": result}
        except Exception as e:
            return {**state, "errors": state.get("errors", []) + [f"CitizenAgent: {e}"]}

    def _generate_final_report(self, state: AnalysisState) -> AnalysisState:
        policy = state.get("policy_analysis", {})
        impact = state.get("impact_analysis", {})
        risk = state.get("risk_analysis", {})
        stakeholder = state.get("stakeholder_analysis", {})

        report = {
            "policy_name": policy.get("policy_name", "Unknown Policy"),
            "doc_id": state["doc_id"],
            "executive_summary": policy.get("summary", ""),
            "objectives": policy.get("objectives", []),
            "stakeholders_identified": policy.get("stakeholders", []),
            "key_provisions": policy.get("key_provisions", []),
            "impact_score": impact.get("overall_impact_score", {}),
            "top_benefits": impact.get("economic_impact", {}).get("positive", [])[:3],
            "top_risks": risk.get("risks", [])[:5],
            "overall_risk_level": risk.get("overall_risk_level", "Unknown"),
            "mitigation_strategies": risk.get("mitigation_strategies", []),
            "stakeholder_impact": stakeholder,
            "errors": state.get("errors", []),
            "agents_run": [
                "Policy Understanding Agent",
                "Impact Analysis Agent",
                "Risk Assessment Agent",
            ] + (["Citizen Guidance Agent"] if stakeholder else []),
        }

        return {**state, "final_report": report}

    def _should_run_stakeholder(self, state: AnalysisState) -> str:
        return "stakeholder" if state.get("stakeholder") else "report"

    # ── Public API ────────────────────────────────────────────────────────

    def run_full_analysis(self, doc_id: str, stakeholder: Optional[str] = None) -> dict:
        """Run complete multi-agent analysis pipeline."""
        print(f"\n[Orchestrator] Starting full analysis for doc_id='{doc_id}'")
        initial_state = AnalysisState(
            doc_id=doc_id,
            stakeholder=stakeholder,
            policy_analysis=None,
            impact_analysis=None,
            risk_analysis=None,
            stakeholder_analysis=None,
            final_report=None,
            errors=[],
        )
        final_state = self.graph.invoke(initial_state)
        print(f"[Orchestrator] ✓ Analysis complete. Errors: {final_state.get('errors', [])}")
        return final_state.get("final_report", {})

    def run_agent_only(self, doc_id: str, agent: str, stakeholder: str = None) -> dict:
        """Run a single specific agent."""
        agents = {
            "policy": lambda: self.policy_agent.analyze(doc_id),
            "impact": lambda: self.impact_agent.analyze(doc_id),
            "risk": lambda: self.risk_agent.analyze(doc_id),
            "citizen": lambda: self.citizen_agent.simulate_stakeholder_impact(doc_id, stakeholder or "Student"),
        }
        fn = agents.get(agent.lower())
        if not fn:
            return {"error": f"Unknown agent: {agent}"}
        return fn()
