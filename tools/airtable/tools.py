"""
Airtable tools for Google ADK agents.
"""
from typing import Optional, List, Dict, Any
from tools.airtable.applicants import (
    create_applicant as _create_applicant,
    get_applicant as _get_applicant,
    update_applicant as _update_applicant,
    find_applicants as _find_applicants
)
from tools.airtable.pipeline import (
    create_pipeline_record as _create_pipeline,
    get_pipeline_record as _get_pipeline,
    update_pipeline_record as _update_pipeline,
    find_pipeline_by_thread_id as _find_pipeline_by_thread
)
from tools.airtable.interactions import log_interaction as _log_interaction
from tools.airtable.contractors import create_contractor as _create_contractor
from shared.models.applicant import ApplicantCreate, ApplicantUpdate
from shared.models.pipeline import PipelineCreate, PipelineUpdate


def airtable_create_applicant(
    applicant_data: dict,
    initiated_by: str,
    reason: str
) -> str:
    """Create a new applicant record in Airtable.
    
    Args:
        applicant_data: Dictionary with applicant fields (name, email, phone, etc.)
        initiated_by: Who is initiating this creation (agent name or user email)
        reason: Explicit reason for creating this applicant record
        
    Returns:
        Record ID of the created applicant
    """
    data = ApplicantCreate(**applicant_data)
    return _create_applicant(
        data=data,
        initiated_by=initiated_by,
        reason=reason
    )


def airtable_get_applicant(record_id: str) -> Optional[dict]:
    """Get an applicant by record ID.
    
    Args:
        record_id: Airtable record ID
        
    Returns:
        Applicant data or None
    """
    applicant = _get_applicant(record_id)
    return applicant.model_dump() if applicant else None


def airtable_update_applicant(
    record_id: str,
    updates: dict,
    initiated_by: str,
    reason: str
) -> bool:
    """Update an applicant record.
    
    Args:
        record_id: Airtable record ID
        updates: Dictionary of fields to update
        initiated_by: Who is initiating this update (agent name or user email)
        reason: Explicit reason for updating this applicant record
        
    Returns:
        True if successful
    """
    data = ApplicantUpdate(**updates)
    return _update_applicant(
        record_id=record_id,
        data=data,
        initiated_by=initiated_by,
        reason=reason
    )


def airtable_find_applicants(formula: Optional[str] = None) -> List[dict]:
    """Find applicants matching criteria.
    
    Args:
        formula: Airtable formula (e.g., "{Email} = 'test@example.com'")
        
    Returns:
        List of applicant records
    """
    applicants = _find_applicants(formula=formula)
    return [a.model_dump() for a in applicants]


def airtable_create_pipeline(
    applicant_id: str,
    initiated_by: str,
    reason: str,
    stage: str = "New"
) -> str:
    """Create a new pipeline record for an applicant.
    
    Args:
        applicant_id: Linked applicant record ID
        initiated_by: Who is initiating this creation (agent name or user email)
        reason: Explicit reason for creating this pipeline record
        stage: Initial pipeline stage
        
    Returns:
        Record ID of the created pipeline record
    """
    data = PipelineCreate(applicant=applicant_id, pipeline_stage=stage)
    return _create_pipeline(
        data=data,
        initiated_by=initiated_by,
        reason=reason
    )


def airtable_get_pipeline(record_id: str) -> Optional[dict]:
    """Get a pipeline record by ID.
    
    Args:
        record_id: Airtable record ID
        
    Returns:
        Pipeline data or None
    """
    pipeline = _get_pipeline(record_id)
    return pipeline.model_dump() if pipeline else None


def airtable_update_pipeline(
    record_id: str,
    updates: dict,
    initiated_by: str,
    reason: str
) -> bool:
    """Update a pipeline record.
    
    Args:
        record_id: Airtable record ID
        updates: Dictionary of fields to update
        initiated_by: Who is initiating this update (agent name or user email)
        reason: Explicit reason for updating this pipeline record
        
    Returns:
        True if successful
    """
    data = PipelineUpdate(**updates)
    return _update_pipeline(
        record_id=record_id,
        data=data,
        initiated_by=initiated_by,
        reason=reason
    )


def airtable_find_pipeline_by_thread(thread_id: str) -> Optional[dict]:
    """Find pipeline record by Gmail thread ID.
    
    Args:
        thread_id: Gmail thread ID
        
    Returns:
        Pipeline data or None
    """
    pipeline = _find_pipeline_by_thread(thread_id)
    return pipeline.model_dump() if pipeline else None


def airtable_log_interaction(
    applicant_id: str,
    interaction_type: str,
    direction: str,
    channel: str,
    summary: str
) -> str:
    """Log an interaction with an applicant.
    
    Args:
        applicant_id: Applicant record ID
        interaction_type: Type (System, Email, Phone Call, etc.)
        direction: Inbound, Outbound, or System
        channel: Gmail, Calendar, Drive, Chat, or Manual
        summary: Text summary of the interaction
        
    Returns:
        Record ID of the interaction log
    """
    return _log_interaction(
        applicant_id=applicant_id,
        interaction_type=interaction_type,
        direction=direction,
        channel=channel,
        summary=summary
    )


def airtable_create_contractor(applicant_id: str, contractor_data: dict) -> str:
    """Create a contractor record from an applicant.
    
    Args:
        applicant_id: Linked applicant record ID
        contractor_data: Additional contractor fields
        
    Returns:
        Record ID of the created contractor
    """
    return _create_contractor(applicant_id, contractor_data)


# Export all tools
ALL_AIRTABLE_TOOLS = [
    airtable_create_applicant,
    airtable_get_applicant,
    airtable_update_applicant,
    airtable_find_applicants,
    airtable_create_pipeline,
    airtable_get_pipeline,
    airtable_update_pipeline,
    airtable_find_pipeline_by_thread,
    airtable_log_interaction,
    airtable_create_contractor
]

