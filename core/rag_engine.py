from __future__ import annotations

from typing import List, Optional

from groq import Groq

from core.config import (
    GROQ_API_KEY,
    LLM_MODEL,
    TEMPERATURE,
    MAX_RETRIEVAL_DOCS,
)
from core.knowledge_base import PolicyKnowledgeBase


class RAGEngine:
    """
    Core Retrieval-Augmented Generation engine.
    Handles context retrieval + LLM-powered answer generation.
    """

    def __init__(self, knowledge_base: PolicyKnowledgeBase):
        self.kb = knowledge_base
        self.client = Groq(api_key=GROQ_API_KEY)
        self.chat_history: List[dict] = []

    def _generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=TEMPERATURE,
            max_tokens=1024,
        )

        return response.choices[0].message.content

    # ── Core RAG Query ────────────────────────────────────────────────────

    def query(
        self,
        question: str,
        doc_ids: Optional[List[str]] = None,
        n_results: int = MAX_RETRIEVAL_DOCS,
        system_prompt: Optional[str] = None,
    ) -> dict:
        """
        Full RAG pipeline: retrieve → augment → generate.
        Returns {answer, sources, context_used}.
        """

        chunks = self.kb.query(
            question,
            n_results=n_results,
            doc_ids=doc_ids,
        )

        if not chunks:
            return {
                "answer": (
                    "I couldn't find relevant information in the uploaded "
                    "policy documents. Please upload a policy PDF first."
                ),
                "sources": [],
                "context_used": "",
            }

        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i} — {chunk['filename']} "
                f"(relevance: {chunk['score']:.2f})]\n"
                f"{chunk['text']}"
            )

        context = "\n\n---\n\n".join(context_parts)

        base_system = system_prompt or """
You are PolicyLens, an expert AI assistant specializing in government policy analysis.

You provide accurate, clear, and actionable answers based strictly on the provided policy documents.

Always cite which document or section your answer is based on.

If the answer is not in the context, clearly state that.
"""

        prompt = f"""
{base_system}

POLICY DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

Provide a clear, structured answer based on the context above.
"""

        answer = self._generate(prompt)

        return {
            "answer": answer,
            "sources": chunks,
            "context_used": context,
        }

    # ── Chat Mode ─────────────────────────────────────────────────────────

    def chat(
        self,
        message: str,
        doc_ids: Optional[List[str]] = None,
    ) -> dict:
        """Multi-turn conversational RAG."""

        self.chat_history.append(
            {
                "role": "user",
                "content": message,
            }
        )

        history_context = ""

        if len(self.chat_history) > 2:
            recent = self.chat_history[-4:-1]

            history_context = (
                "Previous conversation:\n"
                + "\n".join(
                    f"{m['role'].capitalize()}: {m['content']}"
                    for m in recent
                )
                + "\n\n"
            )

        augmented_question = (
            history_context
            + f"Current question: {message}"
        )

        result = self.query(
            augmented_question,
            doc_ids=doc_ids,
        )

        self.chat_history.append(
            {
                "role": "assistant",
                "content": result["answer"],
            }
        )

        return result

    def reset_chat(self):
        self.chat_history = []

    # ── Structured Generation ─────────────────────────────────────────────

    def generate_structured(self, prompt: str) -> str:
        """Generate text without retrieval."""
        return self._generate(prompt)

    def generate_json(self, prompt: str) -> str:
        """Generate JSON-only response."""

        full_prompt = (
            prompt
            + "\n\nRespond ONLY with valid JSON. "
            + "No markdown. No explanation."
        )

        text = self._generate(full_prompt).strip()

        if text.startswith("```"):
            text = text.split("```")[1]

            if text.startswith("json"):
                text = text[4:]

        return text.strip()