"""
ui/app.py — Main Streamlit application entry point
Run with: streamlit run ui/app.py
"""
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

st.set_page_config(
    page_title="PolicyLens — AI Policy Analyst",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "PolicyLens: Agentic RAG for Government Policy Analysis",
    }
)

# ── Custom CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@400;600&family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: #f8f9fb;
    }
    h1, h2, h3 {
        font-family: 'IBM Plex Serif', serif !important;
    }
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .risk-high { color: #dc2626; font-weight: 600; }
    .risk-medium { color: #d97706; font-weight: 600; }
    .risk-low { color: #16a34a; font-weight: 600; }
    .agent-badge {
        display: inline-block;
        background: #eff6ff;
        color: #1d4ed8;
        border: 1px solid #bfdbfe;
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 0.8rem;
        margin: 2px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
    }
    .stTextArea textarea {
        font-family: 'Inter', sans-serif;
    }
    div[data-testid="stSidebarContent"] {
        background: #1e2433;
        color: #e2e8f0;
    }
    div[data-testid="stSidebarContent"] .stCheckbox label {
        color: #e2e8f0 !important;
    }
    div[data-testid="stSidebarContent"] h2, 
    div[data-testid="stSidebarContent"] h3 {
        color: #f1f5f9 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Initialize Session State ──────────────────────────────────────────────
from core.knowledge_base import PolicyKnowledgeBase
from core.rag_engine import RAGEngine
from agents.orchestrator import PolicyAnalysisOrchestrator
from utils.comparison_engine import PolicyComparisonEngine
from utils.timeline_extractor import TimelineExtractor
from evaluation.ragas_evaluator import RAGASEvaluator

@st.cache_resource
def init_system():
    kb = PolicyKnowledgeBase()
    rag = RAGEngine(kb)
    orchestrator = PolicyAnalysisOrchestrator(rag, kb)
    comparison = PolicyComparisonEngine(rag, kb)
    timeline = TimelineExtractor(rag)
    evaluator = RAGASEvaluator(rag, kb)
    return kb, rag, orchestrator, comparison, timeline, evaluator

kb, rag, orchestrator, comparison_engine, timeline_extractor, evaluator = init_system()

# Store in session state for pages to access
st.session_state["kb"] = kb
st.session_state["rag"] = rag
st.session_state["orchestrator"] = orchestrator
st.session_state["comparison_engine"] = comparison_engine
st.session_state["timeline_extractor"] = timeline_extractor
st.session_state["evaluator"] = evaluator

# ── Landing Page ──────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; padding: 60px 0 40px 0;'>
    <div style='font-size: 3.5rem; margin-bottom: 12px;'>🏛️</div>
    <h1 style='font-size: 2.8rem; font-weight: 700; margin: 0; color: #1e293b;'>PolicyLens</h1>
    <p style='font-size: 1.2rem; color: #64748b; margin-top: 8px;'>
        AI-Powered Government Policy Analysis & Impact Assessment
    </p>
</div>
""", unsafe_allow_html=True)

# Feature cards
col1, col2, col3, col4 = st.columns(4)
features = [
    ("💬", "Policy Chat", "Ask anything about uploaded policies using RAG"),
    ("🤖", "Agent Analysis", "4 AI agents: Policy · Impact · Risk · Citizen"),
    ("🔀", "Compare Policies", "GitHub-style diff between two policy docs"),
    ("👥", "Stakeholder Sim", "Impact scores for 6 stakeholder types"),
]
for col, (icon, title, desc) in zip([col1, col2, col3, col4], features):
    with col:
        st.markdown(f"""
        <div class='metric-card' style='text-align:center; min-height:120px;'>
            <div style='font-size:2rem;'>{icon}</div>
            <div style='font-weight:600; color:#1e293b; margin:4px 0;'>{title}</div>
            <div style='font-size:0.8rem; color:#64748b;'>{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Quick stats
docs = kb.documents
if docs:
    st.markdown(f"**{len(docs)} document(s) indexed** — Use the navigation on the left to begin analysis.")
else:
    st.info("👈 Start by uploading a policy PDF in the sidebar, then navigate to any page using the left menu.")

st.markdown("""
### 🚀 Quick Start
1. **Upload** a government policy PDF in the sidebar
2. **Chat** with it on the *Policy Chat* page
3. **Run agents** for deep analysis on the *Agent Analysis* page
4. **Simulate stakeholder impact** on the *Stakeholder Simulator* page
5. **Compare** two versions of a policy on the *Policy Comparison* page
""")
