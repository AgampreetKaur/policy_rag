"""
ui/pages/6__Evaluation.py — RAGAS evaluation dashboard
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
import pandas as pd
from ui.components.sidebar import render_sidebar
from ui.components.charts import eval_gauge, eval_bar

st.set_page_config(page_title="RAG Evaluation — PolicyLens", page_icon="📊", layout="wide")

kb = st.session_state.get("kb")
evaluator = st.session_state.get("evaluator")

if not kb or not evaluator:
    st.error("Please launch the app from `ui/app.py`")
    st.stop()

selected_ids = render_sidebar(kb)

st.title("RAG Evaluation Dashboard")
st.caption("Measure RAG quality using RAGAS-inspired metrics: Faithfulness · Context Relevance · Answer Relevance")

# ── Metric Explanations ────────────────────────────────────────────────────
with st.expander(" What do these metrics mean?"):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ** Faithfulness**  
        Are the generated answers grounded in the retrieved context?  
        High score = answers don't hallucinate facts.
        """)
    with col2:
        st.markdown("""
        **📎 Context Relevance**  
        Are the retrieved document chunks actually relevant to the question?  
        High score = retrieval is on target.
        """)
    with col3:
        st.markdown("""
        ** Answer Relevance**  
        Does the answer actually address what was asked?  
        High score = responses are on-topic and complete.
        """)

if not selected_ids:
    st.warning("Please select at least one document.")
    st.stop()

docs = [kb.get_doc_info(d) for d in selected_ids if kb.get_doc_info(d)]
doc_map = {d["title"]: d["doc_id"] for d in docs}

selected_title = st.selectbox("Select Document to Evaluate", list(doc_map.keys()))
doc_id = doc_map[selected_title]

# ── Custom Questions ────────────────────────────────────────────────────────
st.subheader(" Evaluation Questions")
use_custom = st.checkbox("Add custom evaluation questions")
custom_questions = []

if use_custom:
    st.markdown("Enter up to 5 questions (one per line):")
    custom_text = st.text_area("Custom questions", height=120,
                               placeholder="What are the eligibility criteria?\nWhat is the budget allocated?\n...")
    if custom_text.strip():
        custom_questions = [q.strip() for q in custom_text.strip().split("\n") if q.strip()][:5]

# ── Run Evaluation ─────────────────────────────────────────────────────────
cache_key = f"eval_{doc_id}_{hash(str(custom_questions))}"
col1, col2 = st.columns([1, 4])
with col1:
    eval_btn = st.button(" Run Evaluation", type="primary")

st.markdown("> ⚠️ Evaluation makes multiple LLM calls. For 5-8 questions, this takes ~60-90 seconds.")

if eval_btn or cache_key in st.session_state:
    if eval_btn:
        questions = custom_questions if custom_questions else None
        with st.status(" Running RAGAS evaluation...", expanded=True) as status:
            st.write(f"Generating {'custom' if questions else 'auto-generated'} evaluation questions...")
            st.write("Running faithfulness checks...")
            st.write("Running context relevance scoring...")
            st.write("Running answer relevance scoring...")
            result = evaluator.evaluate(doc_id, questions=questions)
            st.session_state[cache_key] = result
            status.update(label=" Evaluation complete!", state="complete")
    else:
        result = st.session_state[cache_key]

    # ── Results ────────────────────────────────────────────────────────────
    st.markdown("---")
    metrics = result.get("metrics", {})
    grade = result.get("grade", "N/A")
    num_q = result.get("num_questions", 0)

    # Grade banner
    grade_colors = {"A": "#16a34a", "B": "#2563eb", "C": "#d97706", "D": "#dc2626", "F": "#991b1b"}
    grade_letter = grade[0] if grade else "?"
    grade_color = grade_colors.get(grade_letter, "#6b7280")

    st.markdown(f"""
    <div style='background:white; border:2px solid {grade_color}; border-radius:16px;
                padding:20px; text-align:center; margin:16px 0;'>
        <div style='font-size:3rem; color:{grade_color}; font-weight:700;'>{grade_letter}</div>
        <div style='font-size:1rem; color:#64748b;'>{grade}</div>
        <div style='font-size:0.85rem; color:#94a3b8; margin-top:4px;'>
            Based on {num_q} evaluation questions
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Gauges ────────────────────────────────────────────────────────────
    g1, g2, g3 = st.columns(3)
    with g1:
        faith = metrics.get("faithfulness", {})
        st.plotly_chart(eval_gauge(faith.get("mean", 0), "Faithfulness"), use_container_width=True)
    with g2:
        ctx = metrics.get("context_relevance", {})
        st.plotly_chart(eval_gauge(ctx.get("mean", 0), "Context Relevance"), use_container_width=True)
    with g3:
        ans = metrics.get("answer_relevance", {})
        st.plotly_chart(eval_gauge(ans.get("mean", 0), "Answer Relevance"), use_container_width=True)

    # ── Bar Chart ──────────────────────────────────────────────────────────
    display_metrics = {
        "Faithfulness": metrics.get("faithfulness", {}),
        "Context Relevance": metrics.get("context_relevance", {}),
        "Answer Relevance": metrics.get("answer_relevance", {}),
    }
    st.plotly_chart(eval_bar(display_metrics), use_container_width=True)

    # ── Detailed Results Table ─────────────────────────────────────────────
    st.subheader("📋 Per-Question Results")
    samples = result.get("samples", [])
    if samples:
        df = pd.DataFrame([{
            "Question": s["question"][:80] + "..." if len(s["question"]) > 80 else s["question"],
            "Faithfulness": f"{s['faithfulness']:.2f}",
            "Context Rel.": f"{s['context_relevance']:.2f}",
            "Answer Rel.": f"{s['answer_relevance']:.2f}",
            "Overall": f"{s['overall']:.2f}",
        } for s in samples])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Expandable answers
        st.subheader("🔍 Detailed Answers")
        for i, s in enumerate(samples):
            with st.expander(f"Q{i+1}: {s['question'][:60]}..."):
                st.markdown(f"**Answer Preview:**  \n{s['answer_preview']}")
                col_f, col_c, col_a = st.columns(3)
                col_f.metric("Faithfulness", f"{s['faithfulness']:.2f}")
                col_c.metric("Context Rel.", f"{s['context_relevance']:.2f}")
                col_a.metric("Answer Rel.", f"{s['answer_relevance']:.2f}")

    # ── Download ───────────────────────────────────────────────────────────
    import json
    st.download_button(
        "📥 Download Evaluation Report (JSON)",
        data=json.dumps(result, indent=2),
        file_name=f"eval_{selected_title.replace(' ', '_')}.json",
        mime="application/json",
    )
