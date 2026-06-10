"""
ui/components/sidebar.py — Sidebar for document management
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.document_processor import DocumentProcessor
from core.knowledge_base import PolicyKnowledgeBase


def render_sidebar(kb: PolicyKnowledgeBase) -> list:
    """Render sidebar with document upload and management. Returns selected doc_ids."""

    st.sidebar.markdown("""
    <div style='text-align:center; padding: 12px 0 8px 0;'>
        <span style='font-size:2rem;'>🏛️</span><br>
        <span style='font-size:1.2rem; font-weight:700; letter-spacing:1px;'>PolicyLens</span><br>
        <span style='font-size:0.7rem; color:#888; letter-spacing:2px;'>AI POLICY ANALYST</span>
    </div>
    <hr style='margin:8px 0;'>
    """, unsafe_allow_html=True)

    # ── Upload Section ────────────────────────────────────────────────────
    st.sidebar.subheader("📄 Upload Policy")
    uploaded_files = st.sidebar.file_uploader(
        "Upload PDF(s)",
        type=["pdf"],
        accept_multiple_files=True,
        key="pdf_uploader",
        label_visibility="collapsed"
    )

    if uploaded_files:
        processor = DocumentProcessor()
        for uploaded_file in uploaded_files:
            file_bytes = uploaded_file.read()
            # Check if already indexed
            import hashlib
            file_hash = hashlib.md5(file_bytes).hexdigest()[:12]
            doc_id = f"doc_{file_hash}"
            if kb.get_doc_info(doc_id):
                st.sidebar.success(f"✓ {uploaded_file.name[:25]}... already indexed")
                continue

            with st.sidebar.status(f"Indexing {uploaded_file.name[:20]}..."):
                doc = processor.process_bytes(file_bytes, uploaded_file.name)
                kb.add_document(doc)
            st.sidebar.success(f"✓ Indexed: {uploaded_file.name[:25]}")
            st.rerun()

    # ── Document List ─────────────────────────────────────────────────────
    st.sidebar.subheader("📚 Knowledge Base")
    documents = kb.documents

    if not documents:
        st.sidebar.info("No documents yet. Upload a policy PDF to begin.")
        return []

    selected_ids = []
    for doc in documents:
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            checked = st.checkbox(
                f"📄 {doc['title'][:22]}",
                value=True,
                key=f"doc_sel_{doc['doc_id']}",
                help=f"{doc['pages']} pages · {doc['chunk_count']} chunks"
            )
        with col2:
            if st.button("🗑️", key=f"del_{doc['doc_id']}", help="Remove"):
                kb.remove_document(doc["doc_id"])
                st.rerun()

        if checked:
            selected_ids.append(doc["doc_id"])

    # ── Stats ─────────────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"<div style='font-size:0.75rem; color:#888;'>"
        f"📊 {len(documents)} documents · {sum(d['chunk_count'] for d in documents)} chunks"
        f"</div>",
        unsafe_allow_html=True
    )

    return selected_ids
