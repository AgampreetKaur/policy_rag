"""
ui/pages/5__Timeline_View.py — Policy timeline extraction and visualization
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from ui.components.sidebar import render_sidebar
from ui.components.charts import policy_timeline

st.set_page_config(page_title="Policy Timeline — PolicyLens", page_icon="📅", layout="wide")

kb = st.session_state.get("kb")
timeline_extractor = st.session_state.get("timeline_extractor")

if not kb or not timeline_extractor:
    st.error("Please launch the app from `ui/app.py`")
    st.stop()

selected_ids = render_sidebar(kb)

st.title(" Policy Timeline Generator")
st.caption("Automatically extract deadlines, milestones, and implementation phases")

if not selected_ids:
    st.warning("Please select at least one document.")
    st.stop()

docs = [kb.get_doc_info(d) for d in selected_ids if kb.get_doc_info(d)]
doc_map = {d["title"]: d["doc_id"] for d in docs}

selected_title = st.selectbox("Select Document", list(doc_map.keys()))
doc_id = doc_map[selected_title]

cache_key = f"timeline_{doc_id}"

col1, col2 = st.columns([1, 4])
with col1:
    extract_btn = st.button(" Extract Timeline", type="primary")

if extract_btn or cache_key in st.session_state:
    if extract_btn:
        with st.spinner("Extracting dates and milestones from policy..."):
            result = timeline_extractor.extract(doc_id)
            st.session_state[cache_key] = result
    else:
        result = st.session_state[cache_key]

    events = result.get("events", [])

    if not events:
        st.warning("No specific dates or timelines found in this document.")
        st.markdown("**Raw extraction:**")
        st.markdown(result.get("raw_extraction", ""))
    else:
        st.success(f"Found **{len(events)} timeline events**")

        # ── Plotly Timeline ───────────────────────────────────────────────
        st.plotly_chart(policy_timeline(events), use_container_width=True)

        # ── Legend ────────────────────────────────────────────────────────
        type_colors = {
            "deadline": "#ef4444", "milestone": "#3b82f6",
            "implementation": "#8b5cf6", "application": "#22c55e", "review": "#f59e0b"
        }
        legend_html = " ".join(
            f"<span style='display:inline-block; background:{c}; color:white; "
            f"padding:2px 10px; border-radius:12px; font-size:0.75rem; margin:2px;'>{t.title()}</span>"
            for t, c in type_colors.items()
        )
        st.markdown(legend_html, unsafe_allow_html=True)

        st.markdown("---")

        # ── Timeline Cards ────────────────────────────────────────────────
        st.subheader(" All Timeline Events")

        # Group by type
        from collections import defaultdict
        by_type = defaultdict(list)
        for ev in events:
            by_type[ev.get("type", "other")].append(ev)

        tab_names = [t.title() for t in by_type.keys()]
        if tab_names:
            tabs = st.tabs(["All"] + tab_names)
            with tabs[0]:
                for ev in events:
                    color = type_colors.get(ev.get("type", "milestone"), "#6b7280")
                    st.markdown(
                        f"<div style='background:white; border-left:4px solid {color}; "
                        f"border:1px solid #e5e7eb; border-left:4px solid {color}; "
                        f"border-radius:8px; padding:12px 16px; margin:6px 0;'>"
                        f"<b style='color:{color};'>{ev.get('date', 'Date TBD')}</b> — "
                        f"{ev.get('event', '')} "
                        f"<span style='font-size:0.75rem; color:#94a3b8;'>[{ev.get('importance', 'medium')}]</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

            for i, (type_name, type_events) in enumerate(by_type.items()):
                with tabs[i + 1]:
                    for ev in type_events:
                        color = type_colors.get(type_name, "#6b7280")
                        st.markdown(
                            f"<div style='background:white; border-left:4px solid {color}; "
                            f"border:1px solid #e5e7eb; border-radius:8px; padding:12px 16px; margin:6px 0;'>"
                            f"<b>{ev.get('date', 'Date TBD')}</b> — {ev.get('event', '')}"
                            f"</div>",
                            unsafe_allow_html=True
                        )

    # ── Raw AI Extraction ─────────────────────────────────────────────────
    with st.expander("📝 Raw AI Extraction"):
        st.markdown(result.get("raw_extraction", ""))
