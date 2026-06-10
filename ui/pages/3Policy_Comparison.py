"""
ui/pages/3__Policy_Comparison.py — GitHub-style policy diff
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from ui.components.sidebar import render_sidebar

st.set_page_config(page_title="Compare Policies — PolicyLens", page_icon="🔀", layout="wide")

kb = st.session_state.get("kb")
comparison_engine = st.session_state.get("comparison_engine")

if not kb or not comparison_engine:
    st.error("Please launch the app from `ui/app.py`")
    st.stop()

selected_ids = render_sidebar(kb)

st.title(" Policy Comparison Engine")
st.caption("GitHub-style diff between two government policy documents")

docs = kb.documents
if len(docs) < 2:
    st.warning("Upload at least **2 policy documents** to enable comparison.")
    st.info("Example: Upload 'Budget 2024.pdf' and 'Budget 2025.pdf'")
    st.stop()

# ── Document Selection ─────────────────────────────────────────────────────
doc_map = {d["title"]: d["doc_id"] for d in docs}
titles = list(doc_map.keys())

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### 📄 Policy A (Older / Baseline)")
    title_a = st.selectbox("Select Policy A", titles, index=0, key="pol_a")
with col2:
    st.markdown("#### 📄 Policy B (Newer / Revised)")
    remaining = [t for t in titles if t != title_a]
    title_b = st.selectbox("Select Policy B", remaining, index=0 if remaining else None, key="pol_b")

if not title_b:
    st.info("Please upload more documents to compare.")
    st.stop()

doc_id_a = doc_map[title_a]
doc_id_b = doc_map[title_b]

compare_btn = st.button("⚡ Compare Policies", type="primary")

cache_key = f"comparison_{doc_id_a}_{doc_id_b}"

if compare_btn or cache_key in st.session_state:
    if compare_btn:
        with st.spinner(f"Comparing '{title_a}' with '{title_b}'..."):
            result = comparison_engine.compare(doc_id_a, doc_id_b)
            st.session_state[cache_key] = result
    else:
        result = st.session_state[cache_key]

    # ── Comparison Header ─────────────────────────────────────────────────
    col_a, arrow_col, col_b = st.columns([5, 1, 5])
    with col_a:
        st.markdown(f"""
        <div style='background:#f0fdf4; border:1px solid #86efac; border-radius:8px; padding:12px; text-align:center;'>
            <b>📄 {title_a}</b>
        </div>
        """, unsafe_allow_html=True)
    with arrow_col:
        st.markdown("<div style='text-align:center; padding:12px; font-size:1.5rem;'>→</div>", unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""
        <div style='background:#eff6ff; border:1px solid #93c5fd; border-radius:8px; padding:12px; text-align:center;'>
            <b>📄 {title_b}</b>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── AI Summary ────────────────────────────────────────────────────────
    st.subheader(" AI Comparison Summary")
    st.markdown(result.get("ai_summary", ""))

    # ── Objectives Diff ───────────────────────────────────────────────────
    st.subheader(" Objectives Diff")
    obj_diff = result.get("objectives_diff", {})

    col_add, col_rem = st.columns(2)
    with col_add:
        st.markdown("####  Added / New Objectives")
        added = obj_diff.get("added", [])
        if added:
            for obj in added:
                st.markdown(
                    f"<div style='background:#f0fdf4; border-left:4px solid #22c55e; "
                    f"padding:8px 12px; margin:4px 0; border-radius:4px;'>+ {obj}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No new objectives detected")

    with col_rem:
        st.markdown("####  Removed / Missing Objectives")
        removed = obj_diff.get("removed", [])
        if removed:
            for obj in removed:
                st.markdown(
                    f"<div style='background:#fef2f2; border-left:4px solid #ef4444; "
                    f"padding:8px 12px; margin:4px 0; border-radius:4px;'>- {obj}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No removed objectives detected")

    # Retained
    retained = obj_diff.get("retained", [])
    if retained:
        with st.expander(f"✓ {len(retained)} objectives retained in both"):
            for obj in retained:
                st.markdown(f"= {obj}")

    # ── Provisions Diff ───────────────────────────────────────────────────
    st.subheader(" Provisions & Subsidies Comparison")
    prov = result.get("provisions_diff", {})

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown(f"**{title_a}**")
        for line in prov.get("lines_a", []):
            st.markdown(f"• {line}")
    with col_r:
        st.markdown(f"**{title_b}**")
        for line in prov.get("lines_b", []):
            st.markdown(f"• {line}")

    # ── Budget Comparison ─────────────────────────────────────────────────
    st.subheader(" Budget & Financial Comparison")
    budget = result.get("budget_diff", {})
    col_ba, col_bb = st.columns(2)
    with col_ba:
        st.markdown(f"**{title_a} — Budget**")
        st.info(budget.get("policy_a_budget", "Not found"))
    with col_bb:
        st.markdown(f"**{title_b} — Budget**")
        st.info(budget.get("policy_b_budget", "Not found"))

    # ── Text Diff ─────────────────────────────────────────────────────────
    text_diff = result.get("text_diff_sample", [])
    if text_diff:
        with st.expander(" Raw Text Diff (first 50 lines)"):
            diff_html = []
            for line in text_diff:
                if line.startswith("+++") or line.startswith("---"):
                    diff_html.append(f"<span style='color:#6b7280; font-weight:600;'>{line}</span>")
                elif line.startswith("+"):
                    diff_html.append(f"<span style='color:#16a34a; background:#f0fdf4;'>{line}</span>")
                elif line.startswith("-"):
                    diff_html.append(f"<span style='color:#dc2626; background:#fef2f2;'>{line}</span>")
                elif line.startswith("@@"):
                    diff_html.append(f"<span style='color:#7c3aed;'>{line}</span>")
                else:
                    diff_html.append(f"<span style='color:#374151;'>{line}</span>")

            st.markdown(
                "<pre style='font-family:monospace; font-size:0.8rem; "
                "background:#f8fafc; padding:12px; border-radius:8px; overflow-x:auto;'>"
                + "<br>".join(diff_html) + "</pre>",
                unsafe_allow_html=True
            )
