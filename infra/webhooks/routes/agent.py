"""
Agent endpoint for direct HTTP invocation.

Provides HTTP interface to invoke the Applicant Analysis Agent directly.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
from agents.applicant_analysis.agent_adk import process_resume
from shared.logging.logger import setup_logger
from shared.logging.audit import log_workflow_execution

logger = setup_logger(__name__)

router = APIRouter()


class AgentRequest(BaseModel):
    """Request model for agent invocation."""
    file_id: str = Field(..., description="Google Drive file ID of the resume PDF")
    filename: str = Field(default="resume.pdf", description="Original filename")


class AgentResponse(BaseModel):
    """Response model for agent invocation."""
    success: bool
    applicant_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    icc_file_id: Optional[str] = None
    applicant_name: Optional[str] = None
    baseline_verdict: Optional[str] = None
    error: Optional[str] = None


@router.post("/process-resume", response_model=AgentResponse)
async def process_resume_endpoint(request: AgentRequest):
    """
    Process a resume using the Applicant Analysis Agent.
    
    This endpoint invokes the ADK-based agent to:
    1. Download resume from Google Drive
    2. Parse resume and extract information
    3. Analyze candidate fit
    4. Create Airtable records
    5. Generate ICC report
    6. Publish completion event
    
    Args:
        request: Contains file_id and filename
        
    Returns:
        AgentResponse with success status and results
        
    Raises:
        HTTPException: If processing fails
    """
    logger.info(f"Agent HTTP endpoint invoked: {request.filename} ({request.file_id})")
    
    try:
        # Log workflow start
        log_workflow_execution(
            workflow_name="applicant_analysis",
            event_type="http_request",
            event_data=request.dict(),
            status="started"
        )
        
        # Invoke agent
        result = process_resume(
            file_id=request.file_id,
            filename=request.filename
        )
        
        # Log result
        if result['success']:
            logger.info(f"✓ Resume processed successfully via HTTP")
            logger.info(f"  Applicant ID: {result.get('applicant_id')}")
            logger.info(f"  Applicant Name: {result.get('applicant_name')}")
            logger.info(f"  Verdict: {result.get('baseline_verdict')}")
            
            log_workflow_execution(
                workflow_name="applicant_analysis",
                event_type="http_request",
                event_data=request.dict(),
                status="completed",
                result=result
            )
        else:
            logger.error(f"✗ Resume processing failed: {result.get('error')}")
            
            log_workflow_execution(
                workflow_name="applicant_analysis",
                event_type="http_request",
                event_data=request.dict(),
                status="failed",
                result=result
            )
        
        return AgentResponse(**result)
        
    except Exception as e:
        error_msg = f"Agent processing error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        log_workflow_execution(
            workflow_name="applicant_analysis",
            event_type="http_request",
            event_data=request.dict(),
            status="error",
            result={'error': error_msg}
        )
        
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/health")
async def agent_health():
    """Health check for agent endpoint."""
    return {
        "status": "healthy",
        "agent": "applicant_analysis",
        "version": "1.0.0"
    }

