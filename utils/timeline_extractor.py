"""
utils/timeline_extractor.py — Extract policy deadlines, milestones, and dates
"""
from __future__ import annotations

import re
import json
from typing import List

from core.rag_engine import RAGEngine


MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    "Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

DATE_PATTERNS = [
    r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b',
    r'\b(' + '|'.join(MONTH_NAMES) + r')\s+\d{1,2},?\s+\d{4}\b',
    r'\b\d{1,2}\s+(' + '|'.join(MONTH_NAMES) + r')\s+\d{4}\b',
    r'\b(' + '|'.join(MONTH_NAMES) + r')\s+\d{4}\b',
    r'\bQ[1-4]\s+\d{4}\b',
    r'\bFY\s*\d{4}[-–]\d{2,4}\b',
]


class TimelineExtractor:
    """
    Extracts dates, deadlines, and milestones from policy documents.
    Returns structured timeline events for visualization.
    """

    def __init__(self, rag_engine: RAGEngine):
        self.rag = rag_engine

    def extract(self, doc_id: str) -> dict:
        """Extract all timeline events from a policy document."""
        # Use RAG to find date-related content
        result = self.rag.query(
            "List ALL dates, deadlines, milestones, implementation phases, and timelines mentioned. "
            "For each, provide: the date and what happens on that date.",
            doc_ids=[doc_id],
            n_results=7
        )

        # Also extract with AI to get structured JSON
        structured_events = self._extract_structured(doc_id)

        # Parse raw text for additional dates
        raw_events = self._parse_from_text(result["answer"])

        # Merge and deduplicate
        all_events = self._merge_events(structured_events, raw_events)

        return {
            "events": all_events,
            "raw_extraction": result["answer"],
            "event_count": len(all_events),
        }

    def _extract_structured(self, doc_id: str) -> List[dict]:
        """Ask the LLM to return structured JSON timeline."""
        prompt = """Extract all dates, deadlines, and milestones from this policy document.
Return a JSON array of objects with this exact format:
[
  {
    "date": "Month Year or specific date",
    "event": "What happens on this date",
    "type": "deadline|milestone|implementation|application|review",
    "importance": "high|medium|low"
  }
]
If no dates are found, return an empty array []."""

        result = self.rag.query(prompt, doc_ids=[doc_id], n_results=7,
                                system_prompt="Extract dates and events as structured JSON only.")
        try:
            text = result["answer"]
            start = text.find("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                events = json.loads(text[start:end])
                return [e for e in events if isinstance(e, dict) and "date" in e and "event" in e]
        except Exception:
            pass
        return []

    def _parse_from_text(self, text: str) -> List[dict]:
        """Parse dates from raw text using regex."""
        events = []
        lines = text.split("\n")
        for line in lines:
            if not line.strip():
                continue
            has_date = any(re.search(pattern, line, re.IGNORECASE) for pattern in DATE_PATTERNS)
            if has_date:
                clean = line.strip().lstrip("•-*–123456789. ").strip()
                if len(clean) > 10:
                    events.append({
                        "date": self._extract_date_from_line(clean),
                        "event": clean,
                        "type": self._classify_event(clean),
                        "importance": "medium",
                    })
        return events

    def _extract_date_from_line(self, line: str) -> str:
        """Extract the date portion from a line."""
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(0)
        return "Date mentioned"

    def _classify_event(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["deadline", "last date", "by", "before", "submit"]):
            return "deadline"
        if any(w in text_lower for w in ["launch", "start", "begin", "commence", "open"]):
            return "milestone"
        if any(w in text_lower for w in ["apply", "application", "register", "enroll"]):
            return "application"
        if any(w in text_lower for w in ["review", "evaluate", "assess", "report"]):
            return "review"
        return "implementation"

    def _merge_events(self, structured: List[dict], raw: List[dict]) -> List[dict]:
        """Merge and deduplicate events, prefer structured ones."""
        all_events = list(structured)
        existing_events = {e["event"].lower()[:30] for e in structured}
        for ev in raw:
            key = ev["event"].lower()[:30]
            if key not in existing_events:
                all_events.append(ev)
                existing_events.add(key)

        # Add index for ordering
        for i, ev in enumerate(all_events):
            ev["index"] = i

        return all_events
