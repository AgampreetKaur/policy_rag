"""
core/config.py — Central configuration for PolicyLens
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", str(DATA_DIR / "chroma_db"))
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── LLM ───────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))

# ── Embeddings ────────────────────────────────────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── Chunking ──────────────────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
MAX_RETRIEVAL_DOCS = int(os.getenv("MAX_RETRIEVAL_DOCS", "5"))

# ── Stakeholder Profiles ──────────────────────────────────────────────────
STAKEHOLDER_PROFILES = {
    "Student": {
        "icon": "🎓",
        "focus": "education benefits, scholarships, skill development, loans",
        "concerns": "tuition costs, employment prospects, digital access"
    },
    "Farmer": {
        "icon": "🌾",
        "focus": "agricultural subsidies, MSP, irrigation, crop insurance",
        "concerns": "input costs, market access, climate risk, debt"
    },
    "MSME Owner": {
        "icon": "🏭",
        "focus": "credit access, tax relief, export incentives, compliance burden",
        "concerns": "cash flow, GST, labor laws, market competition"
    },
    "Startup Founder": {
        "icon": "🚀",
        "focus": "innovation grants, tax holidays, regulatory sandbox, funding",
        "concerns": "compliance overhead, talent acquisition, IP protection"
    },
    "Teacher": {
        "icon": "📚",
        "focus": "salary revisions, training programs, infrastructure, digital tools",
        "concerns": "workload, assessment reform, career progression"
    },
    "Manufacturer": {
        "icon": "⚙️",
        "focus": "PLI schemes, import duties, infrastructure, energy costs",
        "concerns": "input costs, supply chain, environmental compliance"
    },
}

# ── Risk Categories ───────────────────────────────────────────────────────
RISK_CATEGORIES = ["Implementation", "Compliance", "Budget", "Political", "Social", "Technical"]

RISK_COLORS = {
    "High": "#ef4444",
    "Medium": "#f59e0b",
    "Low": "#22c55e",
}
