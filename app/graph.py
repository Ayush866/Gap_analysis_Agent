# app/graph.py
import json
from typing import Dict, List
from langgraph.graph import StateGraph, END
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage # Use message structure

from app.config import llm_fast, llm_reasoning
from app.schemas import GapAnalysisState
from app.utils import load_and_chunk_document
from app.vector_store import create_vector_store

# --- NODE 1: Document Processor ---
def process_documents(state: GapAnalysisState):
    print(f"--- Processing: {state['reg_doc_path']} & {state['int_doc_path']} ---")
    
    # Load Internal
    internal_chunks = load_and_chunk_document(state["int_doc_path"])
    if not internal_chunks:
        raise ValueError("Failed to load Internal Policy document.")

    # Load Regulatory
    reg_chunks = load_and_chunk_document(state["reg_doc_path"])
    if not reg_chunks:
        raise ValueError("Failed to load Regulatory document.")
    
    return {
        "internal_policy_chunks": [d.page_content for d in internal_chunks],
        "reg_chunks_temp": reg_chunks 
    }

# Inside extract_requirements in app/graph.py
def extract_requirements(state: GapAnalysisState):
    reg_chunks = state.get("reg_chunks_temp", [])
    
    if not reg_chunks:
        # One last attempt to load if state lost the data
        print("Empty state detected, attempting emergency reload...")
        reg_chunks = load_and_chunk_document(state["reg_doc_path"])

    if not reg_chunks:
        print("CRITICAL: Still no text found.")
        return {"regulatory_requirements": [], "status": "failed_no_text"}

    text_context = "\n\n".join([c.page_content for c in reg_chunks[:10]])
    
    # FIXED PROMPT: Enforce JSON format more strictly
    parser = JsonOutputParser()
    
    prompt_template = """
    You are an expert Compliance Officer. 
    Your task is to extract actionable requirements from the provided Regulatory Text.

    RULES:
    1. Return ONLY a JSON array. Do not include markdown formatting (like ```json).
    2. Do not add conversational text.
    3. If the text contains no requirements, return an empty array [].
    
    JSON FORMAT:
    [
        {{
            "id": "REQ-001",
            "text": "Exact requirement text...",
            "type": "mandatory",
            "section": "3.1"
        }}
    ]

    REGULATORY TEXT:
    {text}
    """

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["text"]
    )
    
    chain = prompt | llm_fast | parser

    try:
        requirements = chain.invoke({"text": text_context})
        print(f"DEBUG: Extracted {len(requirements)} requirements.")
    except Exception as e:
        print(f"CRITICAL JSON ERROR: {e}")
        # Fallback: create a dummy requirement if parsing fails, so the pipeline doesn't break
        requirements = [{
            "id": "ERR-001", 
            "text": "Manual Review Required - Automated extraction failed.", 
            "type": "manual", 
            "section": "N/A"
        }]
        
    return {"regulatory_requirements": requirements}

# --- NODE 3: Gap Analyzer ---
def analyze_gaps(state: GapAnalysisState):
    print("--- Analyzing Gaps ---")
    requirements = state["regulatory_requirements"]
    internal_doc_path = state["int_doc_path"]
    
    # Re-load chunks for vector store (since we don't persist store in state)
    internal_chunks = load_and_chunk_document(internal_doc_path)
    if not internal_chunks:
        return {"identified_gaps": []}
        
    vector_store = create_vector_store(internal_chunks)
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    
    identified_gaps = []
    
    for req in requirements:
        # Skip dummy errors
        if req['id'] == "ERR-001":
            continue

        relevant_docs = retriever.invoke(req['text'])
        context_text = "\n".join([d.page_content for d in relevant_docs])
        
        prompt = PromptTemplate(
            template="""
            Compare the Regulatory Requirement against the Internal Policy.
            
            Regulatory: "{req_text}" ({req_type})
            Internal Policy Context:
            {context}
            
            Analyze for gaps.
            Return STRICT JSON:
            {{
                "status": "compliant | missing | partial | conflicting",
                "coverage_text": "Evidence from internal policy or 'None'",
                "severity": "critical | high | medium | low",
                "confidence_score": 0.9,
                "recommendation": "Action to take"
            }}
            """,
            input_variables=["req_text", "req_type", "context"]
        )
        
        # Use Reasoning Model (70b)
        chain = prompt | llm_reasoning | JsonOutputParser()
        
        try:
            analysis = chain.invoke({
                "req_text": req['text'],
                "req_type": req['type'],
                "context": context_text or "No relevant sections found."
            })
            
            gap_record = {
                "id": req['id'],
                "regulatory_reference": req,
                "internal_coverage": analysis,
                "severity": analysis.get("severity", "medium"),
                "confidence_score": analysis.get("confidence_score", 0.5),
                "recommendation": analysis.get("recommendation", "Review manually.")
            }
            identified_gaps.append(gap_record)
            print(f"Analyzed {req['id']}: {analysis.get('status')}")
            
        except Exception as e:
            print(f"Error analyzing req {req['id']}: {e}")
            
    return {"identified_gaps": identified_gaps}

# --- NODE 4: Report Generator ---
def generate_report(state: GapAnalysisState):
    print("--- Generating Executive Summary ---")
    gaps = state.get("identified_gaps", [])
    
    if not gaps:
        print("WARNING: No gaps found to generate report!")
        return {
            "executive_summary": {
                "overall_compliance_score": 0,
                "total_requirements": 0,
                "gaps_identified": 0,
                "critical_gaps": 0
            }
        }
    
    total = len(gaps)
    compliant = sum(1 for g in gaps if g.get("internal_coverage", {}).get("status") == "compliant")
    critical = sum(1 for g in gaps if g.get("severity") == "critical")
    score = (compliant / total) * 100 if total > 0 else 0
    
    summary = {
        "overall_compliance_score": round(score, 2),
        "total_requirements": total,
        "gaps_identified": total - compliant,
        "critical_gaps": critical
    }
    
    print(f"Summary generated: {summary}")
    return {"executive_summary": summary}


# --- Graph Construction ---
workflow = StateGraph(GapAnalysisState)

workflow.add_node("process_docs", process_documents)
workflow.add_node("extract_reqs", extract_requirements)
workflow.add_node("analyze_gaps", analyze_gaps)
workflow.add_node("generate_report", generate_report)

workflow.set_entry_point("process_docs")
workflow.add_edge("process_docs", "extract_reqs")
workflow.add_edge("extract_reqs", "analyze_gaps")
workflow.add_edge("analyze_gaps", "generate_report")
workflow.add_edge("generate_report", END)

app_graph = workflow.compile()