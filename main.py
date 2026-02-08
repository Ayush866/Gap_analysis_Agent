import shutil
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.graph import app_graph

app = FastAPI(title="Gap Analysis Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_documents(
    regulatory_doc: UploadFile = File(...),
    internal_doc: UploadFile = File(...)
):
    """
    Synchronous endpoint that processes documents and returns results immediately.
    Perfect for demos - no polling needed!
    """
    temp_dir = None
    try:
        # Create temporary directory for this request
        import uuid
        request_id = str(uuid.uuid4())
        temp_dir = f"temp_files/{request_id}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save uploaded files
        reg_path = f"{temp_dir}/reg_{regulatory_doc.filename}"
        int_path = f"{temp_dir}/int_{internal_doc.filename}"
        
        print(f"[{request_id}] Saving files...")
        with open(reg_path, "wb") as buffer:
            shutil.copyfileobj(regulatory_doc.file, buffer)
        with open(int_path, "wb") as buffer:
            shutil.copyfileobj(internal_doc.file, buffer)
        
        print(f"[{request_id}] Starting analysis...")
        
        # Prepare inputs for the agent
        inputs = {
            "reg_doc_path": reg_path,
            "int_doc_path": int_path,
            "regulatory_requirements": [],
            "identified_gaps": [],
            "errors": []
        }
        
        # Run the agent synchronously
        final_state = app_graph.invoke(inputs)
        print(f"[{request_id}] Analysis completed. State keys: {final_state.keys()}")
        
        # Validate that we have required data
        if "executive_summary" not in final_state:
            print(f"[{request_id}] WARNING: No executive_summary in final state!")
            raise ValueError("Executive summary generation failed")
        
        # Format the response
        response_data = {
            "status": "success",
            "message": "Analysis completed successfully",
            "data": {
                "analysis_metadata": {
                    "regulatory_document": regulatory_doc.filename,
                    "internal_document": internal_doc.filename,
                    "analysis_date": get_current_date(),
                    "agent_version": "1.0",
                    "request_id": request_id
                },
                "executive_summary": final_state.get("executive_summary", "No summary generated"),
                "gaps": final_state.get("identified_gaps", []),
                "regulatory_requirements": final_state.get("regulatory_requirements", [])
            }
        }
        
        print(f"[{request_id}] Returning results to client")
        return JSONResponse(content=response_data, status_code=200)
        
    except Exception as e:
        print(f"ERROR during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return error response
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Analysis failed: {str(e)}",
                "data": None
            },
            status_code=500
        )
    
    finally:
        # Cleanup temporary files
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                print(f"Failed to cleanup temp directory: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Gap Analysis Agent API"}

def get_current_date():
    """Get current date in YYYY-MM-DD format"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)