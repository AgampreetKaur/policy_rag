"""
utils/export_utils.py — Export analysis reports to PDF and JSON
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


def export_to_json(report: dict, output_path: Optional[str] = None) -> str:
    """Export analysis report to JSON file."""
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        policy_name = report.get("policy_name", "report").replace(" ", "_")[:30]
        output_path = f"/tmp/{policy_name}_{timestamp}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return output_path


def export_to_text_report(report: dict) -> str:
    """Generate a formatted text report from analysis results."""
    lines = []

    def h1(text):
        lines.append(f"\n{'='*60}")
        lines.append(f"  {text.upper()}")
        lines.append(f"{'='*60}")

    def h2(text):
        lines.append(f"\n{'─'*50}")
        lines.append(f"  {text}")
        lines.append(f"{'─'*50}")

    def bullet(text, indent=2):
        lines.append(f"{'  '*indent}• {text}")

    # Header
    lines.append(f"\n{'█'*60}")
    lines.append(f"  POLICYLENS — AI POLICY ANALYSIS REPORT")
    lines.append(f"  Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}")
    lines.append(f"{'█'*60}")

    # Policy Name
    h1(report.get("policy_name", "Policy Analysis"))

    # Executive Summary
    h2("Executive Summary")
    summary = report.get("executive_summary", "No summary available.")
    lines.append(f"\n{summary}\n")

    # Objectives
    h2("Policy Objectives")
    for obj in report.get("objectives", []):
        bullet(obj)

    # Key Provisions
    h2("Key Provisions")
    for prov in report.get("key_provisions", []):
        bullet(prov)

    # Impact Score
    impact_score = report.get("impact_score", {})
    if impact_score:
        h2("Impact Assessment")
        lines.append(f"\n  Overall Impact Score: {impact_score.get('score', 'N/A')}/10")
        lines.append(f"  Sentiment: {impact_score.get('sentiment', 'N/A')}")
        lines.append(f"\n  Top Benefits:")
        for b in report.get("top_benefits", []):
            bullet(b)

    # Risk Assessment
    h2("Risk Assessment")
    lines.append(f"\n  Overall Risk Level: {report.get('overall_risk_level', 'N/A')}")
    lines.append(f"\n  Identified Risks:")
    for risk in report.get("top_risks", []):
        bullet(f"[{risk.get('severity', '?')}] {risk.get('category', '')}: {risk.get('description', '')}")

    lines.append(f"\n  Mitigation Strategies:")
    for m in report.get("mitigation_strategies", []):
        bullet(m)

    # Stakeholder Impact
    stakeholder = report.get("stakeholder_impact", {})
    if stakeholder and stakeholder.get("stakeholder"):
        h2(f"Stakeholder Impact: {stakeholder.get('icon', '')} {stakeholder.get('stakeholder', '')}")
        lines.append(f"\n  Impact Score: {stakeholder.get('impact_score', 'N/A')}/10")
        lines.append(f"  Verdict: {stakeholder.get('verdict', '')}")
        lines.append(f"\n  Benefits:")
        for b in stakeholder.get("benefits", []):
            bullet(b)
        lines.append(f"\n  Risks:")
        for r in stakeholder.get("risks", []):
            bullet(r)
        lines.append(f"\n  Required Actions:")
        for a in stakeholder.get("required_actions", []):
            bullet(a)

    # Agents Run
    h2("Analysis Metadata")
    lines.append(f"\n  Agents Used: {', '.join(report.get('agents_run', []))}")
    errors = report.get("errors", [])
    if errors:
        lines.append(f"\n  Errors: {', '.join(errors)}")

    lines.append(f"\n{'═'*60}")
    lines.append(f"  End of Report — PolicyLens")
    lines.append(f"{'═'*60}\n")

    return "\n".join(lines)


def report_to_bytes(report: dict) -> bytes:
    """Convert report to downloadable bytes."""
    text = export_to_text_report(report)
    return text.encode("utf-8")
