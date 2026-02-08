from typing import List, Optional, Dict, TypedDict, Annotated
from pydantic import BaseModel, Field

# --- API Models ---
class GapAnalysisResponse(BaseModel):
    job_id: str
    status: str
    message: str

# --- LangGraph State ---
class GapAnalysisState(TypedDict):
    # Inputs
    reg_doc_path: str
    int_doc_path: str
    
    # Processing Data
    regulatory_requirements: List[Dict] # Extracted requirements
    internal_policy_chunks: List[str]   # Chunked internal doc text
    
    # Analysis Results
    identified_gaps: List[Dict]
    executive_summary: Dict
    
    # Metadata
    status: str
    errors: List[str]