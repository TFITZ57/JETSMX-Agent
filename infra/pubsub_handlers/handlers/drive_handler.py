"""
Drive event handler for Pub/Sub.

Handles Drive file upload events and routes them to appropriate agents.
Specifically handles resume uploads for the Applicant Analysis Agent.
"""
from typing import Dict, Any
from agents.applicant_analysis.agent_adk import process_resume
from shared.logging.logger import setup_logger
from shared.logging.audit import log_workflow_execution

logger = setup_logger(__name__)


def handle_resume_upload(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle new resume upload from Drive.
    
    This function is triggered when a new PDF is uploaded to the HR/Resumes folder.
    It invokes the Applicant Analysis Agent (ADK) to process the resume.
    
    Args:
        event_data: Drive event data containing file_id, name, mime_type, etc.
        
    Returns:
        Result dictionary with success status and details
    """
    file_id = event_data.get('file_id')
    filename = event_data.get('name')
    mime_type = event_data.get('mime_type', '')
    
    logger.info(f"Handling resume upload: {filename} ({file_id})")
    
    # Validate this is a PDF
    if not mime_type == 'application/pdf' and not filename.lower().endswith('.pdf'):
        logger.warning(f"Skipping non-PDF file: {filename} (mime_type: {mime_type})")
        return {
            'success': False,
            'error': 'Not a PDF file',
            'file_id': file_id,
            'filename': filename
        }
    
    try:
        # Log workflow start
        log_workflow_execution(
            workflow_name="applicant_analysis",
            event_type="resume_upload",
            event_data=event_data,
            status="started"
        )
        
        # Invoke ADK agent
        result = process_resume(file_id=file_id, filename=filename)
        
        # Log result
        if result['success']:
            logger.info(f"✓ Resume processed successfully: {result.get('applicant_id')}")
            logger.info(f"  Applicant: {result.get('applicant_name')}")
            logger.info(f"  Verdict: {result.get('baseline_verdict')}")
            logger.info(f"  Pipeline ID: {result.get('pipeline_id')}")
            logger.info(f"  ICC File ID: {result.get('icc_file_id')}")
            
            log_workflow_execution(
                workflow_name="applicant_analysis",
                event_type="resume_upload",
                event_data=event_data,
                status="completed",
                result=result
            )
        else:
            logger.error(f"✗ Resume processing failed: {result.get('error')}")
            
            log_workflow_execution(
                workflow_name="applicant_analysis",
                event_type="resume_upload",
                event_data=event_data,
                status="failed",
                result=result
            )
        
        return result
        
    except Exception as e:
        error_msg = f"Unexpected error handling resume upload: {str(e)}"
        logger.error(error_msg)
        
        log_workflow_execution(
            workflow_name="applicant_analysis",
            event_type="resume_upload",
            event_data=event_data,
            status="error",
            result={'error': error_msg}
        )
        
        return {
            'success': False,
            'error': error_msg,
            'file_id': file_id,
            'filename': filename
        }


def handle_drive_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route Drive events to appropriate handlers based on folder and file type.
    
    Args:
        event_data: Drive event data
        
    Returns:
        Result dictionary
    """
    file_id = event_data.get('file_id')
    filename = event_data.get('name', '')
    parents = event_data.get('parents', [])
    
    logger.info(f"Processing Drive event: {filename} ({file_id})")
    
    # Check if this is in the resumes folder
    # In production, you would check the parent folder ID
    # For now, we'll check if filename suggests it's a resume
    is_resume = any([
        'resume' in filename.lower(),
        'cv' in filename.lower(),
        # Add more heuristics or check parent folder ID
    ])
    
    if is_resume or event_data.get('folder_type') == 'resumes':
        return handle_resume_upload(event_data)
    
    # Handle other Drive event types (transcripts, etc.)
    # For now, just log and return
    logger.info(f"No handler for Drive file: {filename}")
    return {
        'success': True,
        'message': 'No handler configured for this file type',
        'file_id': file_id
    }

