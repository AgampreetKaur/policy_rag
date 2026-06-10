
"""
ui/pages/2__Agent_Analysis.py — Multi-agent orchestration dashboard
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from ui.components.sidebar import render_sidebar
from ui.components.charts import risk_heatmap, impact_radar
from utils.export_utils import report_to_bytes
from core.config import STAKEHOLDER_PROFILES, RISK_COLORS

st.set_page_config(page_title="Agent Analysis — PolicyLens", page_icon="🤖", layout="wide")

kb = st.session_state.get("kb")
orchestrator = st.session_state.get("orchestrator")

if not kb or not orchestrator:
    st.error("Please launch the app from `ui/app.py`")
    st.stop()

selected_ids = render_sidebar(kb)

# ── Page ──────────────────────────────────────────────────────────────────
st.title(" Multi-Agent Policy Analysis")
st.caption("Run 4 specialized AI agents: Policy Understanding → Impact Analysis → Risk Assessment → Citizen Guidance")

if not selected_ids:
    st.warning("Please select at least one document in the sidebar.")
    st.stop()

docs = [kb.get_doc_info(d) for d in selected_ids if kb.get_doc_info(d)]
doc_options = {d["title"]: d["doc_id"] for d in docs}

# ── Controls ──────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    selected_doc_title = st.selectbox("Select Document to Analyze", list(doc_options.keys()))
    doc_id = doc_options[selected_doc_title]
with col2:
    stakeholder = st.selectbox(
        "Optional: Include Stakeholder Analysis",
        ["None"] + list(STAKEHOLDER_PROFILES.keys())
    )
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button(" Run All Agents", type="primary", use_container_width=True)

# ── Agent Badges ──────────────────────────────────────────────────────────
st.markdown("""
<div style='margin: 8px 0;'>
    <span class='agent-badge'> Policy Understanding</span>
    <span class='agent-badge'> Impact Analysis</span>
    <span class='agent-badge'> Risk Assessment</span>
    <span class='agent-badge'> Citizen Guidance</span>
</div>
""", unsafe_allow_html=True)

# ── Run Analysis ──────────────────────────────────────────────────────────
cache_key = f"report_{doc_id}_{stakeholder}"

if run_btn or cache_key in st.session_state:
    if run_btn:
        with st.status(" Running multi-agent pipeline...", expanded=True) as status:
            st.write(" Running Policy Understanding Agent...")
            st.write(" Running Impact Analysis Agent...")
            st.write(" Running Risk Assessment Agent...")
            if stakeholder != "None":
                st.write(f" Running Citizen Guidance Agent for {stakeholder}...")

            report = orchestrator.run_full_analysis(
                doc_id,
                stakeholder=stakeholder if stakeholder != "None" else None
            )
            st.session_state[cache_key] = report
            status.update(label=" Analysis complete!", state="complete")
    else:
        report = st.session_state[cache_key]

    # ── Results ────────────────────────────────────────────────────────────
    st.markdown("---")

    # Download button
    col_dl, col_spacer = st.columns([1, 4])
    with col_dl:
        st.download_button(
            " Download Report",
            data=report_to_bytes(report),
            file_name=f"{report.get('policy_name', 'report').replace(' ', '_')}_analysis.txt",
            mime="text/plain",
        )

    # Summary metrics
    impact = report.get("impact_score", {})
    risk_level = report.get("overall_risk_level", "N/A")
    risk_color = RISK_COLORS.get(risk_level, "#6b7280")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Objectives Found", len(report.get("objectives", [])))
    m2.metric("Stakeholders ID'd", len(report.get("stakeholders_identified", [])))
    m3.metric("Impact Score", f"{impact.get('score', 'N/A')}/10")
    m4.metric("Risks Found", len(report.get("top_risks", [])))

    # Tabs for each agent output
    tab1, tab2, tab3, tab4 = st.tabs([
        " Policy Summary", " Impact Analysis", " Risk Assessment", " Stakeholder Impact"
    ])

    # Tab 1: Policy Summary
    with tab1:
        st.subheader("Executive Summary")
        st.markdown(report.get("executive_summary", "No summary available."))

        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader(" Policy Objectives")
            for obj in report.get("objectives", []):
                st.markdown(f"• {obj}")

        with col_r:
            st.subheader(" Identified Stakeholders")
            for s in report.get("stakeholders_identified", []):
                if isinstance(s, dict):
                    st.markdown(f"• **{s.get('name', '')}** ({s.get('role', '')}): {s.get('description', '')}")
                else:
                    st.markdown(f"• {s}")

        st.subheader("📌 Key Provisions")
        for p in report.get("key_provisions", []):
            st.markdown(f"✓ {p}")

    # Tab 2: Impact Analysis
    with tab2:
        impact_data = st.session_state.get(f"impact_{doc_id}")

        score_data = report.get("impact_score", {})
        c1, c2, c3 = st.columns(3)
        c1.metric("Impact Score", f"{score_data.get('score', 'N/A')}/10")
        c2.metric("Sentiment", score_data.get("sentiment", "N/A"))
        c3.metric("Positive Points", score_data.get("positive_points", 0))

        st.subheader(" Top Benefits")
        for b in report.get("top_benefits", []):
            st.success(f"✓ {b}")

        if not report.get("top_benefits"):
            st.info("Run full impact analysis for detailed benefits.")

    # Tab 3: Risk Assessment
    with tab3:
        risks = report.get("top_risks", [])
        rl = report.get("overall_risk_level", "N/A")
        color = RISK_COLORS.get(rl, "#6b7280")
        st.markdown(f"**Overall Risk Level:** <span style='color:{color}; font-size:1.2rem;'>{rl}</span>",
                    unsafe_allow_html=True)

        if risks:
            st.plotly_chart(risk_heatmap(risks), use_container_width=True)

            st.subheader("⚠️ Identified Risks")
            for risk in risks:
                sev = risk.get("severity", "Medium")
                col = RISK_COLORS.get(sev, "#6b7280")
                st.markdown(
                    f"<div class='metric-card'>"
                    f"<span style='color:{col}; font-weight:600;'>[{sev}]</span> "
                    f"<b>{risk.get('category', '')}:</b> {risk.get('description', '')}"
                    f"</div>",
                    unsafe_allow_html=True
                )

        st.subheader("🛡️ Mitigation Strategies")
        for m in report.get("mitigation_strategies", []):
            st.markdown(f"→ {m}")

    # Tab 4: Stakeholder Impact
    with tab4:
        sh = report.get("stakeholder_impact", {})
        if sh and sh.get("stakeholder"):
            score = sh.get("impact_score", 5)
            verdict = sh.get("verdict", "")
            icon = sh.get("icon", "👤")

            st.markdown(f"## {icon} {sh.get('stakeholder', '')} Impact Analysis")

            sc_col, verd_col = st.columns([1, 2])
            sc_col.metric("Impact Score", f"{score}/10")
            verd_col.metric("Verdict", verdict)

            c_ben, c_risk = st.columns(2)
            with c_ben:
                st.subheader(" Benefits")
                for b in sh.get("benefits", []):
                    st.success(f"✓ {b}")
            with c_risk:
                st.subheader(" Risks")
                for r in sh.get("risks", []):
                    st.warning(f"⚠ {r}")

            st.subheader(" Required Actions")
            for a in sh.get("required_actions", []):
                st.markdown(f"→ {a}")

            st.subheader(" Eligibility Summary")
            st.info(sh.get("eligibility_summary", ""))
        else:
            st.info("Select a stakeholder type above and re-run to see stakeholder-specific impact.")
