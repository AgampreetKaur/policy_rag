# PolicyLens – Policy Analysis using Agentic RAG

Policy documents are often lengthy, technical, and difficult to interpret for citizens, businesses, and even policymakers. PolicyLens is an Agentic RAG (Retrieval-Augmented Generation) system that helps users explore and understand government policy documents through natural language interactions and specialized AI agents.

The system allows users to upload one or more policy PDFs, ask questions, compare policies, analyze stakeholder impact, identify risks, and extract important timelines from the documents.

---

## Overview

PolicyLens combines a traditional RAG pipeline with a multi-agent workflow to provide more structured and insightful analysis of policy documents.

The application supports:

- Uploading and querying multiple policy PDFs
- Policy summarization and objective extraction
- Policy comparison and change analysis
- Stakeholder impact assessment
- Risk identification and scoring
- Timeline and deadline extraction
- RAG quality evaluation using RAGAS

---

## How It Works

### 1. Document Processing

- Policy PDFs are uploaded by the user
- Documents are cleaned and split into manageable chunks
- Embeddings are generated using Sentence Transformers
- Chunks are stored in ChromaDB for retrieval

### 2. Retrieval-Augmented Generation (RAG)

- Relevant document chunks are retrieved based on the user query
- Retrieved context is provided to Gemini
- Responses are generated using only the retrieved information

### 3. Multi-Agent Analysis

A LangGraph-based orchestrator coordinates multiple specialized agents:

- **Policy Agent** – Generates summaries and extracts key objectives
- **Impact Agent** – Evaluates economic, social, and administrative impact
- **Risk Agent** – Identifies implementation, compliance, and budget-related risks
- **Citizen Agent** – Handles citizen-centric questions and eligibility queries

The outputs from these agents are combined into a comprehensive analysis report.

---

## Project Structure

```text
policy_rag/
├── README.md
├── requirements.txt
├── .env.example
├── main.py

├── core/
│   ├── document_processor.py
│   ├── knowledge_base.py
│   ├── rag_engine.py
│   └── config.py

├── agents/
│   ├── orchestrator.py
│   ├── policy_agent.py
│   ├── impact_agent.py
│   ├── risk_agent.py
│   └── citizen_agent.py

├── ui/
│   ├── app.py
│   ├── pages/
│   └── components/

├── evaluation/
│   ├── ragas_evaluator.py
│   └── test_questions.py

├── utils/
├── data/
└── tests/
```

---

## Technologies Used

- Python
- Streamlit
- FastAPI
- LangGraph
- ChromaDB
- Google Gemini
- Sentence Transformers
- Plotly
- RAGAS

---

## Installation

Clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd policy_rag
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file and add the following configuration:

```env
GEMINI_API_KEY=your_api_key
CHROMA_PERSIST_DIR=./data/chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

---

## Running the Application

### Streamlit Interface

```bash
streamlit run ui/app.py
```

### FastAPI Backend

```bash
uvicorn main:app --reload
```

---

## Features

### Policy Chat

Ask questions about uploaded policy documents and receive responses grounded in the source material.

### Agent Analysis

Generate detailed policy summaries, impact assessments, risk evaluations, and citizen-focused insights using specialized agents.

### Policy Comparison

Compare two policy documents and identify major changes, additions, and differences.

### Stakeholder Impact Simulation

Analyze how different stakeholder groups may be affected by a policy.

### Timeline Extraction

Automatically extract important dates, deadlines, milestones, and implementation schedules.

### RAG Evaluation

Measure retrieval and generation quality using RAGAS metrics.

---

## Evaluation

The project uses RAGAS to assess the quality of generated responses.

Run evaluation using:

```bash
python -m evaluation.ragas_evaluator --policy sample.pdf
```

Metrics tracked include:

- **Faithfulness** – Measures whether answers are supported by the source documents
- **Context Relevance** – Evaluates the relevance of retrieved context
- **Answer Relevance** – Measures how well the generated answer addresses the query

---

## Motivation

I built PolicyLens to explore how Agentic AI and Retrieval-Augmented Generation can improve access to public policy information. Government policies often contain valuable information but are difficult to navigate due to their size and complexity.

This project focuses on making policy documents easier to understand by combining document retrieval with specialized AI agents that provide summaries, impact analysis, risk assessment, and citizen-oriented explanations.

---
## Output
<img width="800" height="550" alt="Screenshot 2026-06-10 at 9 39 16 PM" src="https://github.com/user-attachments/assets/66bd8ff3-bb3f-49aa-8f9b-4f1554d49965" />
<img width="800" height="607" alt="Screenshot 2026-06-10 at 9 39 32 PM" src="https://github.com/user-attachments/assets/b1780080-21d0-408b-8412-6a85b2f3ab33" />
<img width="800" height="617" alt="Screenshot 2026-06-10 at 9 43 42 PM" src="https://github.com/user-attachments/assets/ac13d863-e032-4b55-8cb3-466ce71de74d" />
<img width="800" height="613" alt="Screenshot 2026-06-10 at 9 44 17 PM" src="https://github.com/user-attachments/assets/354d319d-eaf9-4d45-a26d-a1c18e94187a" />
<img width="800" height="623" alt="Screenshot 2026-06-10 at 9 52 04 PM" src="https://github.com/user-attachments/assets/9c381614-33ff-460a-b47c-fde6e3fa7505" />
<img width="800" height="608" alt="Screenshot 2026-06-10 at 9 52 16 PM" src="https://github.com/user-attachments/assets/f24a32b2-7ba0-40ed-92a2-4c5d66f06f7d" />
<img width="800" height="609" alt="Screenshot 2026-06-10 at 9 52 30 PM" src="https://github.com/user-attachments/assets/635a1739-51ff-4cde-be9c-d1dc23b560ce" />








## Future Improvements

- Support for multilingual policy documents
- Advanced stakeholder profiling
- Policy recommendation engine
- Interactive report generation
- Enhanced evaluation benchmarks

---
