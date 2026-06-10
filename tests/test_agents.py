"""
tests/test_agents.py — Unit tests for multi-agent system
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import MagicMock, patch


def make_mock_rag(answer="Test answer", sources=None):
    """Factory for a mock RAGEngine."""
    mock = MagicMock()
    mock.query.return_value = {
        "answer": answer,
        "sources": sources or [],
        "context_used": "some context",
    }
    mock.generate_structured.return_value = answer
    mock.generate_json.return_value = "[]"
    return mock


def make_mock_kb(doc_id="doc_001", title="Test Policy"):
    mock = MagicMock()
    mock.get_doc_info.return_value = {
        "doc_id": doc_id,
        "title": title,
        "filename": "test.pdf",
        "pages": 5,
        "chunk_count": 20,
    }
    return mock


class TestPolicyAgent:
    def test_analyze_returns_expected_keys(self):
        from agents.policy_agent import PolicyUnderstandingAgent
        rag = make_mock_rag(answer='["Increase EV adoption", "Reduce emissions"]')
        kb = make_mock_kb()

        agent = PolicyUnderstandingAgent(rag, kb)
        result = agent.analyze("doc_001")

        assert result["agent"] == "Policy Understanding Agent"
        assert "summary" in result
        assert "objectives" in result
        assert "stakeholders" in result
        assert result["doc_id"] == "doc_001"


class TestRiskAgent:
    def test_severity_estimation(self):
        from agents.risk_agent import RiskAssessmentAgent
        rag = make_mock_rag()
        kb = make_mock_kb()

        agent = RiskAssessmentAgent(rag, kb)
        assert agent._estimate_severity("This is a critical failure risk") == "High"
        assert agent._estimate_severity("Minor administrative overhead") == "Low"
        assert agent._estimate_severity("Some adjustment needed") == "Medium"

    def test_overall_risk_level(self):
        from agents.risk_agent import RiskAssessmentAgent
        rag = make_mock_rag()
        kb = make_mock_kb()
        agent = RiskAssessmentAgent(rag, kb)

        risks_high = [{"severity": "High"}] * 3 + [{"severity": "Low"}] * 2
        assert agent._overall_level(risks_high) == "High"

        risks_medium = [{"severity": "High"}] * 1 + [{"severity": "Low"}] * 5
        assert agent._overall_level(risks_medium) == "Medium"

        risks_low = [{"severity": "Low"}] * 5
        assert agent._overall_level(risks_low) == "Low"


class TestCitizenAgent:
    def test_impact_score_calculation(self):
        from agents.citizen_agent import CitizenGuidanceAgent
        rag = make_mock_rag()
        kb = make_mock_kb()
        agent = CitizenGuidanceAgent(rag, kb)

        # Many benefits, few risks → high score
        score = agent._compute_impact_score(["b1", "b2", "b3", "b4", "b5"], ["r1"])
        assert score > 7.0

        # No benefits, many risks → low score
        score = agent._compute_impact_score([], ["r1", "r2", "r3", "r4"])
        assert score == 0.0

    def test_verdict_mapping(self):
        from agents.citizen_agent import CitizenGuidanceAgent
        rag = make_mock_rag()
        kb = make_mock_kb()
        agent = CitizenGuidanceAgent(rag, kb)

        assert agent._verdict(9.0) == "Highly Beneficial"
        assert agent._verdict(6.0) == "Moderately Beneficial"
        assert agent._verdict(4.5) == "Mixed Impact"
        assert agent._verdict(2.0) == "Potentially Challenging"

    def test_simulate_returns_required_keys(self):
        from agents.citizen_agent import CitizenGuidanceAgent
        rag = make_mock_rag(answer="• Benefit 1\n• Benefit 2\n• Benefit 3")
        kb = make_mock_kb()
        agent = CitizenGuidanceAgent(rag, kb)

        result = agent.simulate_stakeholder_impact("doc_001", "Student")
        required_keys = ["stakeholder", "icon", "impact_score", "benefits", "risks",
                         "required_actions", "eligibility_summary", "verdict"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"


class TestOrchestrator:
    def test_full_pipeline_returns_report(self):
        from agents.orchestrator import PolicyAnalysisOrchestrator
        rag = make_mock_rag(answer='["obj1", "obj2"]')
        kb = make_mock_kb()

        orchestrator = PolicyAnalysisOrchestrator(rag, kb)
        report = orchestrator.run_full_analysis("doc_001")

        assert "policy_name" in report
        assert "agents_run" in report
        assert len(report["agents_run"]) >= 3

    def test_with_stakeholder_runs_citizen_agent(self):
        from agents.orchestrator import PolicyAnalysisOrchestrator
        rag = make_mock_rag(answer="Some policy content")
        kb = make_mock_kb()

        orchestrator = PolicyAnalysisOrchestrator(rag, kb)
        report = orchestrator.run_full_analysis("doc_001", stakeholder="Student")

        assert "Citizen Guidance Agent" in report.get("agents_run", [])
        assert report.get("stakeholder_impact") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
