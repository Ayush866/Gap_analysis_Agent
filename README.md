# 🔍 AI-Powered Gap Analysis Agent

An AI-powered compliance gap analysis system that compares **regulatory policy documents** against **internal policy documents** to identify compliance gaps, inconsistencies, risks, and actionable recommendations.

This project was built as part of a **technical assessment** to demonstrate agent design, document understanding, LLM orchestration, and structured reporting.

---

## 📌 Overview

Organizations must ensure their internal policies align with external regulatory requirements (e.g., GDPR, SOC 2, ISO 27001).  
This system automates that process by:

- Parsing regulatory and internal policy documents
- Extracting compliance requirements
- Mapping internal policy coverage
- Identifying gaps and conflicts
- Generating a structured JSON report and human-readable summary

---

## 🎯 Objectives Covered

✔ Parse and understand regulatory & internal documents  
✔ Extract regulatory requirements and obligations  
✔ Map internal policies to regulatory clauses  
✔ Identify missing, partial, or conflicting coverage  
✔ Generate gap analysis with severity & recommendations  
✔ Provide confidence scores and citations  

---

## 🧠 Agent Architecture

The solution is implemented as a **multi-step agent pipeline using LangGraph**:

### 1️⃣ Document Processor
- Loads PDF, DOCX, TXT documents
- Preserves structure
- Chunks large documents efficiently

### 2️⃣ Requirement Extractor
- Uses an LLM to extract **mandatory regulatory requirements**
- Outputs structured JSON (ID, text, type, section)

### 3️⃣ Policy Mapper & Gap Analyzer
- Uses FAISS vector search to retrieve relevant internal policy sections
- Compares regulatory requirements against internal coverage
- Detects:
  - Missing
  - Partial
  - Conflicting compliance

### 4️⃣ Report Generator
- Computes compliance statistics
- Generates executive summary
- Produces structured, auditable output

---

## 🏗️ Tech Stack

| Layer | Technology |
|-----|-----------|
Backend API | FastAPI |
Agent Orchestration | LangGraph |
LLMs | Groq (LLaMA 3.x) |
Embeddings | HuggingFace (MiniLM) |
Vector Store | FAISS |
Document Parsing | LangChain Loaders |
Frontend (Demo) | HTML + Vanilla JS |

---

## 📂 Project Structure

```text
.
├── app/
│   ├── main.py            # FastAPI entry point
│   ├── graph.py           # LangGraph agent workflow
│   ├── config.py          # LLM & embedding configuration
│   ├── utils.py           # Document loading & chunking
│   ├── vector_store.py    # FAISS vector store
│   └── schemas.py         # State & response schemas
│
├── frontend/
│   └── index.html         # Demo UI
│
├── temp_files/            # Temporary upload storage (runtime)
├── .env.example           # Environment variable template
├── requirements.txt
└── README.md
