"""
ui/components/charts.py — Plotly chart builders for dashboards
"""
from __future__ import annotations

from typing import List
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from core.config import RISK_COLORS, STAKEHOLDER_PROFILES


def risk_heatmap(risks: List[dict]) -> go.Figure:
    """Risk matrix heatmap: Severity × Category."""
    if not risks:
        return _empty_chart("No risk data available")

    categories = list({r["category"] for r in risks})
    severities = ["Low", "Medium", "High"]

    matrix = [[0] * len(categories) for _ in severities]
    for risk in risks:
        s_idx = severities.index(risk.get("severity", "Medium")) if risk.get("severity") in severities else 1
        c_idx = categories.index(risk["category"]) if risk["category"] in categories else 0
        matrix[s_idx][c_idx] += 1

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=categories,
        y=severities,
        colorscale=[[0, "#dcfce7"], [0.5, "#fef9c3"], [1.0, "#fee2e2"]],
        text=[[str(v) if v > 0 else "" for v in row] for row in matrix],
        texttemplate="%{text}",
        showscale=True,
        hoverongaps=False,
    ))
    fig.update_layout(
        title="Risk Heatmap: Severity × Category",
        xaxis_title="Risk Category",
        yaxis_title="Severity",
        height=300,
        margin=dict(t=40, b=40, l=40, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def impact_radar(impact_data: dict) -> go.Figure:
    """Radar chart for multi-dimensional impact scores."""
    categories = ["Economic\n(Positive)", "Economic\n(Negative)", "Social\n(Positive)",
                  "Social\n(Negative)", "Administrative", "Overall Score"]

    econ = impact_data.get("economic_impact", {})
    social = impact_data.get("social_impact", {})
    overall = impact_data.get("overall_impact_score", {})

    values = [
        min(10, len(econ.get("positive", [])) * 2),
        min(10, len(econ.get("negative", [])) * 2),
        min(10, len(social.get("positive", [])) * 2),
        min(10, len(social.get("negative", [])) * 2),
        5,
        overall.get("score", 5),
    ]
    values.append(values[0])  # close loop
    cats = categories + [categories[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=cats, fill='toself',
        fillcolor='rgba(59,130,246,0.15)',
        line=dict(color='#3b82f6', width=2),
        name="Impact"
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        showlegend=False,
        height=360,
        margin=dict(t=30, b=30, l=60, r=60),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def stakeholder_bar(sim_results: List[dict]) -> go.Figure:
    """Horizontal bar chart of stakeholder impact scores."""
    if not sim_results:
        return _empty_chart("No stakeholder data")

    names = [f"{r['icon']} {r['stakeholder']}" for r in sim_results]
    scores = [r["impact_score"] for r in sim_results]
    colors = ["#22c55e" if s >= 7 else "#f59e0b" if s >= 5 else "#ef4444" for s in scores]

    fig = go.Figure(go.Bar(
        x=scores, y=names, orientation='h',
        marker_color=colors,
        text=[f"{s}/10" for s in scores],
        textposition="outside",
    ))
    fig.update_layout(
        title="Impact Score by Stakeholder",
        xaxis=dict(range=[0, 11], title="Impact Score"),
        height=max(250, len(names) * 50),
        margin=dict(t=40, b=40, l=140, r=60),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def policy_timeline(events: List[dict]) -> go.Figure:
    """Plotly timeline/Gantt for policy events."""
    if not events:
        return _empty_chart("No timeline events found")

    type_colors = {
        "deadline": "#ef4444",
        "milestone": "#3b82f6",
        "implementation": "#8b5cf6",
        "application": "#22c55e",
        "review": "#f59e0b",
    }

    fig = go.Figure()
    for i, ev in enumerate(events):
        color = type_colors.get(ev.get("type", "milestone"), "#6b7280")
        fig.add_trace(go.Scatter(
            x=[i], y=[ev.get("type", "Event")],
            mode="markers+text",
            marker=dict(size=16, color=color, symbol="circle"),
            text=[ev.get("date", "")],
            textposition="top center",
            hovertext=ev.get("event", "")[:100],
            hoverinfo="text",
            name=ev.get("type", "event").title(),
            showlegend=False,
        ))

    # Add connector line
    if len(events) > 1:
        fig.add_shape(
            type="line",
            x0=0, x1=len(events)-1,
            y0=0, y1=0,
            yref="paper",
            line=dict(color="#d1d5db", width=2, dash="dot"),
        )

    fig.update_layout(
        title="Policy Timeline",
        xaxis=dict(
            tickvals=list(range(len(events))),
            ticktext=[ev.get("date", f"Event {i+1}")[:15] for i, ev in enumerate(events)],
            tickangle=45,
        ),
        height=350,
        margin=dict(t=40, b=80, l=100, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def eval_gauge(score: float, title: str = "RAG Score") -> go.Figure:
    """Gauge chart for evaluation metrics."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score * 100,
        title={"text": title},
        delta={"reference": 75},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#3b82f6"},
            "steps": [
                {"range": [0, 50], "color": "#fee2e2"},
                {"range": [50, 75], "color": "#fef9c3"},
                {"range": [75, 100], "color": "#dcfce7"},
            ],
            "threshold": {"line": {"color": "red", "width": 3}, "value": 50},
        }
    ))
    fig.update_layout(height=220, margin=dict(t=50, b=20, l=20, r=20),
                      paper_bgcolor="rgba(0,0,0,0)")
    return fig


def eval_bar(metrics: dict) -> go.Figure:
    """Bar chart for all RAGAS metrics."""
    names = list(metrics.keys())
    means = [metrics[k]["mean"] * 100 for k in names]
    colors = ["#22c55e" if v >= 75 else "#f59e0b" if v >= 60 else "#ef4444" for v in means]

    fig = go.Figure(go.Bar(
        x=names, y=means, marker_color=colors,
        text=[f"{v:.1f}%" for v in means], textposition="outside"
    ))
    fig.update_layout(
        title="RAGAS Evaluation Metrics",
        yaxis=dict(range=[0, 110], title="Score (%)"),
        height=300,
        margin=dict(t=40, b=40, l=40, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _empty_chart(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False, font_size=14)
    fig.update_layout(height=200, paper_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig
