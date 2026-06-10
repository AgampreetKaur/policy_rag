"""
ui/pages/1_💬_Policy_Chat.py — Conversational RAG chat interface
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st
from ui.components.sidebar import render_sidebar

st.set_page_config(page_title="Policy Chat — PolicyLens", page_icon="💬", layout="wide")

# ── Init ──────────────────────────────────────────────────────────────────
kb = st.session_state.get("kb")
rag = st.session_state.get("rag")

if not kb or not rag:
    st.error("Please launch the app from `ui/app.py`")
    st.stop()

selected_ids = render_sidebar(kb)

# ── Page ──────────────────────────────────────────────────────────────────
st.title("Policy Chat")
st.caption("Ask questions about your uploaded policy documents.")

if not selected_ids:
    st.warning("Please upload and select at least one policy document in the sidebar.")
    st.stop()

# Show active docs
st.markdown(
    "Searching in: " + ", ".join(
        f"**{kb.get_doc_info(d)['title']}**" for d in selected_ids if kb.get_doc_info(d)
    )
)

# ── Chat History ──────────────────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Suggested questions
if not st.session_state.chat_messages:
    st.markdown("####  Suggested Questions")
    suggestions = [
        "What are the main objectives of this policy?",
        "Who are the primary beneficiaries?",
        "What is the total budget allocated?",
        "What are the eligibility criteria?",
        "What are the key implementation timelines?",
        "What subsidies or benefits are offered?",
    ]
    cols = st.columns(3)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 3]:
            if st.button(suggestion, key=f"sugg_{i}", use_container_width=True):
                st.session_state.chat_messages.append({"role": "user", "content": suggestion})
                st.rerun()

# Display chat history
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander(f"📎 {len(msg['sources'])} source(s) used"):
                for src in msg["sources"]:
                    st.markdown(f"**{src['filename']}** (relevance: {src['score']:.2f})")
                    st.text(src["text"][:300] + "...")

# ── Input ──────────────────────────────────────────────────────────────────
col_input, col_clear = st.columns([5, 1])
with col_clear:
    if st.button("Clear", use_container_width=True):
        st.session_state.chat_messages = []
        rag.reset_chat()
        st.rerun()

if prompt := st.chat_input("Ask anything about the policy..."):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching policy documents..."):
            result = rag.chat(prompt, doc_ids=selected_ids)
            answer = result["answer"]
            sources = result["sources"]

        st.markdown(answer)
        if sources:
            with st.expander(f"📎 {len(sources)} source(s) used"):
                for src in sources:
                    st.markdown(f"**{src['filename']}** (relevance: {src['score']:.2f})")
                    st.text(src["text"][:300] + "...")

    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
