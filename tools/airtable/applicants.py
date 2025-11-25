"""
Applicants table operations.
"""
from typing import Optional, Dict, Any, List
from tools.airtable.client import get_airtable_client
from shared.config.constants import TABLE_APPLICANTS
from shared.models.applicant import ApplicantCreate, ApplicantUpdate, Applicant
from shared.logging.logger import setup_logger
from shared.logging.audit import log_airtable_update

logger = setup_logger(__name__)


def create_applicant(
    data: ApplicantCreate,
    initiated_by: str,
    reason: str
) -> str:
    """
    Create a new applicant record.
    
    Args:
        data: Applicant data
        initiated_by: Who is initiating this creation (agent name or user email)
        reason: Explicit reason for creating this applicant record
        
    Returns:
        Record ID
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_APPLICANTS)
    
    # Convert model to dict and filter None values
    fields = {k: v for k, v in data.model_dump().items() if v is not None}
    
    try:
        record = table.create(fields)
        record_id = record['id']
        
        logger.info(f"Created applicant record: {record_id}")
        log_airtable_update(
            table=TABLE_APPLICANTS,
            record_id=record_id,
            fields_updated=fields,
            initiated_by=initiated_by,
            reason=reason
        )
        
        return record_id
        
    except Exception as e:
        logger.error(f"Failed to create applicant: {str(e)}")
        raise


def get_applicant(record_id: str) -> Optional[Applicant]:
    """
    Get an applicant by record ID.
    
    Args:
        record_id: Airtable record ID
        
    Returns:
        Applicant or None
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_APPLICANTS)
    
    try:
        record = table.get(record_id)
        applicant = Applicant(id=record['id'], **record['fields'])
        return applicant
    except Exception as e:
        logger.error(f"Failed to get applicant {record_id}: {str(e)}")
        return None


def update_applicant(
    record_id: str,
    data: ApplicantUpdate,
    initiated_by: str,
    reason: str
) -> bool:
    """
    Update an applicant record.
    
    Args:
        record_id: Airtable record ID
        data: Fields to update
        initiated_by: Who is initiating this update (agent name or user email)
        reason: Explicit reason for updating this applicant record
        
    Returns:
        True if successful
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_APPLICANTS)
    
    # Convert model to dict and filter None values
    fields = {k: v for k, v in data.model_dump().items() if v is not None}
    
    if not fields:
        logger.warning("No fields to update")
        return False
    
    try:
        # Get current values for audit
        current_record = table.get(record_id)
        before_values = {k: current_record['fields'].get(k) for k in fields.keys()}
        
        # Update record
        table.update(record_id, fields)
        
        logger.info(f"Updated applicant record: {record_id}")
        log_airtable_update(
            table=TABLE_APPLICANTS,
            record_id=record_id,
            fields_updated=fields,
            initiated_by=initiated_by,
            reason=reason,
            before_values=before_values
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update applicant {record_id}: {str(e)}")
        return False


def find_applicants(formula: Optional[str] = None, view: Optional[str] = None) -> List[Applicant]:
    """
    Find applicants matching criteria.
    
    Args:
        formula: Airtable formula (e.g., "{Email} = 'test@example.com'")
        view: View name to use
        
    Returns:
        List of applicants
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_APPLICANTS)
    
    try:
        records = table.all(formula=formula, view=view)
        applicants = [Applicant(id=r['id'], **r['fields']) for r in records]
        return applicants
    except Exception as e:
        logger.error(f"Failed to find applicants: {str(e)}")
        return []

