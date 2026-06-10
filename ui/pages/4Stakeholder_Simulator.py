"""
ui/pages/4__Stakeholder_Simulator.py — Personalized impact simulation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from ui.components.sidebar import render_sidebar
from ui.components.charts import stakeholder_bar
from core.config import STAKEHOLDER_PROFILES

st.set_page_config(page_title="Stakeholder Simulator — PolicyLens", page_icon="👥", layout="wide")

kb = st.session_state.get("kb")
orchestrator = st.session_state.get("orchestrator")

if not kb or not orchestrator:
    st.error("Please launch the app from `ui/app.py`")
    st.stop()

selected_ids = render_sidebar(kb)

st.title(" Stakeholder Impact Simulator")
st.caption("Discover how this policy affects you personally — select your profile")

if not selected_ids:
    st.warning("Please select at least one document.")
    st.stop()

docs = [kb.get_doc_info(d) for d in selected_ids if kb.get_doc_info(d)]
doc_map = {d["title"]: d["doc_id"] for d in docs}

# ── Policy Selection ──────────────────────────────────────────────────────
selected_doc_title = st.selectbox("Select Policy", list(doc_map.keys()))
doc_id = doc_map[selected_doc_title]

# ── Stakeholder Cards ─────────────────────────────────────────────────────
st.subheader("Who are you?")
cols = st.columns(3)
selected_stakeholder = st.session_state.get("selected_stakeholder", None)

for i, (name, profile) in enumerate(STAKEHOLDER_PROFILES.items()):
    with cols[i % 3]:
        is_selected = selected_stakeholder == name
        border = "3px solid #3b82f6" if is_selected else "1px solid #e5e7eb"
        bg = "#eff6ff" if is_selected else "white"

        st.markdown(f"""
        <div style='background:{bg}; border:{border}; border-radius:12px;
                    padding:16px; text-align:center; cursor:pointer; margin-bottom:8px;'>
            <div style='font-size:2rem;'>{profile['icon']}</div>
            <div style='font-weight:600; color:#1e293b;'>{name}</div>
            <div style='font-size:0.75rem; color:#64748b; margin-top:4px;'>{profile['focus'][:50]}...</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Select {name}", key=f"sel_{name}", use_container_width=True,
                     type="primary" if is_selected else "secondary"):
            st.session_state["selected_stakeholder"] = name
            st.rerun()

st.markdown("---")

# ── Run Simulation ────────────────────────────────────────────────────────
if selected_stakeholder:
    profile = STAKEHOLDER_PROFILES[selected_stakeholder]
    cache_key = f"sim_{doc_id}_{selected_stakeholder}"

    col_hdr, col_btn = st.columns([3, 1])
    with col_hdr:
        st.subheader(f"{profile['icon']} Simulating impact for: **{selected_stakeholder}**")
    with col_btn:
        run_sim = st.button("⚡ Simulate", type="primary", use_container_width=True)

    if run_sim or cache_key in st.session_state:
        if run_sim:
            with st.spinner(f"Analyzing policy impact for {selected_stakeholder}..."):
                citizen_agent = orchestrator.citizen_agent
                result = citizen_agent.simulate_stakeholder_impact(doc_id, selected_stakeholder)
                st.session_state[cache_key] = result
        else:
            result = st.session_state[cache_key]

        # ── Impact Score ──────────────────────────────────────────────────
        score = result.get("impact_score", 5)
        verdict = result.get("verdict", "")

        # Score display
        score_pct = int(score * 10)
        bar_color = "#22c55e" if score >= 7 else "#f59e0b" if score >= 5 else "#ef4444"

        st.markdown(f"""
        <div style='background:white; border:1px solid #e5e7eb; border-radius:16px;
                    padding:24px; margin:16px 0; text-align:center;'>
            <div style='font-size:3rem; font-weight:700; color:{bar_color};'>{score}/10</div>
            <div style='font-size:1.1rem; color:#64748b; margin-top:4px;'>{verdict}</div>
            <div style='background:#f1f5f9; border-radius:8px; height:12px; margin-top:12px;'>
                <div style='background:{bar_color}; width:{score_pct}%; height:12px;
                            border-radius:8px; transition:width 0.5s;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Details ────────────────────────────────────────────────────────
        tab_ben, tab_risk, tab_action, tab_elig = st.tabs([
            " Benefits", " Risks", " Actions", " Eligibility"
        ])

        with tab_ben:
            benefits = result.get("benefits", [])
            if benefits:
                for b in benefits:
                    st.success(f"✓ {b}")
            else:
                st.info("No specific benefits identified for this stakeholder type.")

        with tab_risk:
            risks = result.get("risks", [])
            if risks:
                for r in risks:
                    st.warning(f"⚠ {r}")
            else:
                st.info("No specific risks identified for this stakeholder type.")

        with tab_action:
            actions = result.get("required_actions", [])
            if actions:
                for i, a in enumerate(actions, 1):
                    st.markdown(f"**Step {i}.** {a}")
            else:
                st.info("No required actions identified.")

        with tab_elig:
            st.info(result.get("eligibility_summary", "No eligibility information found."))

    st.markdown("---")

    # ── Compare All Stakeholders ───────────────────────────────────────────
    st.subheader(" Compare All Stakeholders")
    if st.button("Run All 6 Stakeholder Simulations", key="run_all"):
        all_results = []
        citizen_agent = orchestrator.citizen_agent
        progress = st.progress(0)
        for i, name in enumerate(STAKEHOLDER_PROFILES.keys()):
            with st.spinner(f"Simulating {name}..."):
                res = citizen_agent.simulate_stakeholder_impact(doc_id, name)
                all_results.append(res)
            progress.progress((i + 1) / len(STAKEHOLDER_PROFILES))
        st.session_state[f"all_sim_{doc_id}"] = all_results
        st.rerun()

    all_sim_key = f"all_sim_{doc_id}"
    if all_sim_key in st.session_state:
        all_results = st.session_state[all_sim_key]
        st.plotly_chart(stakeholder_bar(all_results), use_container_width=True)

        # Summary table
        table_data = []
        for r in all_results:
            table_data.append({
                "Stakeholder": f"{r['icon']} {r['stakeholder']}",
                "Impact Score": f"{r['impact_score']}/10",
                "Verdict": r.get("verdict", ""),
                "Benefits": len(r.get("benefits", [])),
                "Risks": len(r.get("risks", [])),
            })
        import pandas as pd
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
else:
    st.info(" Select your stakeholder profile above to begin the simulation.")
