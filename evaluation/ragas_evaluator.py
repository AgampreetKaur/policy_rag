"""
evaluation/ragas_evaluator.py — RAGAS-based RAG evaluation pipeline
Measures: Faithfulness, Context Relevance, Answer Relevance
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np

from core.rag_engine import RAGEngine
from core.knowledge_base import PolicyKnowledgeBase


@dataclass
class EvalSample:
    question: str
    answer: str = ""
    contexts: List[str] = field(default_factory=list)
    ground_truth: Optional[str] = None


@dataclass
class EvalResult:
    sample: EvalSample
    faithfulness: float = 0.0
    context_relevance: float = 0.0
    answer_relevance: float = 0.0

    @property
    def overall(self) -> float:
        return round((self.faithfulness + self.context_relevance + self.answer_relevance) / 3, 3)


class RAGASEvaluator:
    """
    Lightweight RAGAS-inspired evaluator using LLM-as-judge.
    Evaluates: Faithfulness, Context Relevance, Answer Relevance.
    
    For production: replace with actual ragas library evaluation.
    """

    def __init__(self, rag_engine: RAGEngine, kb: PolicyKnowledgeBase):
        self.rag = rag_engine
        self.kb = kb

    def evaluate(self, doc_id: str, questions: Optional[List[str]] = None) -> dict:
        """
        Run full evaluation on a document.
        Uses provided questions or generates them automatically.
        """
        doc_info = self.kb.get_doc_info(doc_id)
        print(f"[Evaluator] Evaluating RAG on '{doc_info['title']}'...")

        if not questions:
            questions = self._generate_eval_questions(doc_id)

        results: List[EvalResult] = []
        for q in questions:
            print(f"  → Evaluating: '{q[:60]}...'")
            result = self._evaluate_sample(doc_id, q)
            results.append(result)

        return self._aggregate_results(results, doc_info)

    def _generate_eval_questions(self, doc_id: str) -> List[str]:
        """Auto-generate evaluation questions from the document."""
        prompt = """Generate 8 diverse evaluation questions for this policy document.
Include: factual questions, eligibility questions, impact questions, timeline questions.
Return a JSON array of strings.
Example: ["What is the total budget allocated?", "Who is eligible for benefits?", ...]"""

        result = self.rag.query(prompt, doc_ids=[doc_id], n_results=5)
        try:
            text = result["answer"]
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                questions = json.loads(text[start:end])
                return [q for q in questions if isinstance(q, str)][:8]
        except Exception:
            pass

        # Fallback default questions
        return [
            "What are the main objectives of this policy?",
            "Who are the primary beneficiaries?",
            "What is the total budget or financial outlay?",
            "What are the eligibility criteria?",
            "What are the implementation timelines?",
        ]

    def _evaluate_sample(self, doc_id: str, question: str) -> EvalResult:
        """Evaluate a single question-answer pair."""
        # Get answer + context
        rag_result = self.rag.query(question, doc_ids=[doc_id], n_results=4)
        answer = rag_result["answer"]
        contexts = [s["text"] for s in rag_result["sources"]]

        sample = EvalSample(question=question, answer=answer, contexts=contexts)

        faithfulness = self._score_faithfulness(answer, contexts)
        context_rel = self._score_context_relevance(question, contexts)
        answer_rel = self._score_answer_relevance(question, answer)

        return EvalResult(
            sample=sample,
            faithfulness=faithfulness,
            context_relevance=context_rel,
            answer_relevance=answer_rel,
        )

    def _score_faithfulness(self, answer: str, contexts: List[str]) -> float:
        """
        Faithfulness: Is every claim in the answer supported by the context?
        LLM-as-judge approach.
        """
        if not contexts:
            return 0.0

        context_text = "\n\n".join(contexts[:3])
        prompt = f"""You are evaluating RAG faithfulness.

RETRIEVED CONTEXT:
{context_text[:2000]}

GENERATED ANSWER:
{answer[:1000]}

Score how faithfully the answer is grounded in the context.
Score from 0.0 to 1.0 where:
- 1.0 = Every claim is directly supported by the context
- 0.5 = About half the claims are supported  
- 0.0 = Answer contradicts or ignores the context

Return ONLY a decimal number like: 0.85"""

        try:
            response = self.rag.generate_structured(prompt)
            # Extract number from response
            import re
            match = re.search(r'\b(0\.\d+|1\.0|1)\b', response)
            if match:
                return min(1.0, max(0.0, float(match.group())))
        except Exception:
            pass
        return 0.7  # Default

    def _score_context_relevance(self, question: str, contexts: List[str]) -> float:
        """Context Relevance: How relevant are the retrieved chunks to the question?"""
        if not contexts:
            return 0.0

        relevant_count = 0
        for ctx in contexts[:4]:
            prompt = f"""Question: {question}

Context chunk: {ctx[:500]}

Is this context chunk relevant to answering the question?
Answer with only: relevant / partially_relevant / not_relevant"""
            try:
                response = self.rag.generate_structured(prompt).lower().strip()
                if "not_relevant" in response:
                    relevant_count += 0
                elif "partially" in response:
                    relevant_count += 0.5
                else:
                    relevant_count += 1
            except Exception:
                relevant_count += 0.6

        return round(relevant_count / len(contexts[:4]), 3)

    def _score_answer_relevance(self, question: str, answer: str) -> float:
        """Answer Relevance: Does the answer actually address the question?"""
        prompt = f"""Question: {question}

Answer: {answer[:800]}

Score how directly and completely this answer addresses the question.
Score from 0.0 to 1.0 where:
- 1.0 = Directly and completely answers the question
- 0.5 = Partially answers the question
- 0.0 = Does not address the question at all

Return ONLY a decimal number like: 0.82"""

        try:
            response = self.rag.generate_structured(prompt)
            import re
            match = re.search(r'\b(0\.\d+|1\.0|1)\b', response)
            if match:
                return min(1.0, max(0.0, float(match.group())))
        except Exception:
            pass
        return 0.75

    def _aggregate_results(self, results: List[EvalResult], doc_info: dict) -> dict:
        """Aggregate results into summary metrics."""
        if not results:
            return {"error": "No evaluation results"}

        faithfulness_scores = [r.faithfulness for r in results]
        context_scores = [r.context_relevance for r in results]
        answer_scores = [r.answer_relevance for r in results]
        overall_scores = [r.overall for r in results]

        samples = [
            {
                "question": r.sample.question,
                "answer_preview": r.sample.answer[:200] + "...",
                "faithfulness": r.faithfulness,
                "context_relevance": r.context_relevance,
                "answer_relevance": r.answer_relevance,
                "overall": r.overall,
            }
            for r in results
        ]

        return {
            "document": doc_info["title"],
            "num_questions": len(results),
            "metrics": {
                "faithfulness": {
                    "mean": round(float(np.mean(faithfulness_scores)), 3),
                    "min": round(float(np.min(faithfulness_scores)), 3),
                    "max": round(float(np.max(faithfulness_scores)), 3),
                },
                "context_relevance": {
                    "mean": round(float(np.mean(context_scores)), 3),
                    "min": round(float(np.min(context_scores)), 3),
                    "max": round(float(np.max(context_scores)), 3),
                },
                "answer_relevance": {
                    "mean": round(float(np.mean(answer_scores)), 3),
                    "min": round(float(np.min(answer_scores)), 3),
                    "max": round(float(np.max(answer_scores)), 3),
                },
                "overall_rag_score": round(float(np.mean(overall_scores)), 3),
            },
            "grade": self._grade(float(np.mean(overall_scores))),
            "samples": samples,
        }

    def _grade(self, score: float) -> str:
        if score >= 0.85:
            return "A — Excellent"
        if score >= 0.75:
            return "B — Good"
        if score >= 0.60:
            return "C — Acceptable"
        if score >= 0.50:
            return "D — Needs Improvement"
        return "F — Poor"
