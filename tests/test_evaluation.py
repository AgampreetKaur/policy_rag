"""
tests/test_evaluation.py — Tests for RAGAS evaluator
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from unittest.mock import MagicMock


def make_mock_rag():
    mock = MagicMock()
    mock.query.return_value = {
        "answer": "The subsidy amount is ₹50,000 for eligible farmers who own less than 5 acres.",
        "sources": [
            {"text": "Farmers with less than 5 acres are eligible for ₹50,000 subsidy.", "filename": "policy.pdf", "score": 0.9},
            {"text": "The scheme aims to support small and marginal farmers.", "filename": "policy.pdf", "score": 0.85},
        ],
        "context_used": "context text",
    }
    mock.generate_structured.return_value = "0.85"
    return mock


class TestRAGASEvaluator:
    def test_grade_mapping(self):
        from evaluation.ragas_evaluator import RAGASEvaluator
        rag = make_mock_rag()
        kb = MagicMock()
        evaluator = RAGASEvaluator(rag, kb)

        assert evaluator._grade(0.90)[:1] == "A"
        assert evaluator._grade(0.77)[:1] == "B"
        assert evaluator._grade(0.62)[:1] == "C"
        assert evaluator._grade(0.52)[:1] == "D"
        assert evaluator._grade(0.30)[:1] == "F"

    def test_score_faithfulness_returns_float(self):
        from evaluation.ragas_evaluator import RAGASEvaluator
        rag = make_mock_rag()
        kb = MagicMock()
        evaluator = RAGASEvaluator(rag, kb)

        score = evaluator._score_faithfulness(
            "The subsidy is ₹50,000.",
            ["The subsidy amount is ₹50,000 for eligible farmers."]
        )
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_eval_sample_structure(self):
        from evaluation.ragas_evaluator import EvalSample, EvalResult
        sample = EvalSample(
            question="What is the budget?",
            answer="₹10,000 crore",
            contexts=["Budget allocated is ₹10,000 crore."]
        )
        result = EvalResult(
            sample=sample,
            faithfulness=0.9,
            context_relevance=0.85,
            answer_relevance=0.88,
        )
        assert abs(result.overall - (0.9 + 0.85 + 0.88) / 3) < 0.01

    def test_aggregate_results(self):
        from evaluation.ragas_evaluator import RAGASEvaluator, EvalResult, EvalSample
        rag = make_mock_rag()
        kb = MagicMock()
        kb.get_doc_info.return_value = {"title": "Test Policy", "doc_id": "doc_001"}
        evaluator = RAGASEvaluator(rag, kb)

        results = [
            EvalResult(EvalSample("Q1", "A1", ["ctx"]), 0.9, 0.8, 0.85),
            EvalResult(EvalSample("Q2", "A2", ["ctx"]), 0.7, 0.75, 0.8),
        ]
        agg = evaluator._aggregate_results(results, {"title": "Test"})

        assert "metrics" in agg
        assert "faithfulness" in agg["metrics"]
        assert agg["num_questions"] == 2
        assert abs(agg["metrics"]["faithfulness"]["mean"] - 0.8) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
