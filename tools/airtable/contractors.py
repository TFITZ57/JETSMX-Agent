"""
Contractors table operations.
"""
from typing import Optional, Dict, Any
from tools.airtable.client import get_airtable_client
from shared.config.constants import TABLE_CONTRACTORS
from shared.logging.logger import setup_logger
from shared.logging.audit import log_airtable_update

logger = setup_logger(__name__)


def create_contractor(applicant_id: str, contractor_data: Dict[str, Any]) -> str:
    """
    Create a new contractor record from an applicant.
    
    Args:
        applicant_id: Linked applicant record ID
        contractor_data: Additional contractor fields
        
    Returns:
        Record ID
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_CONTRACTORS)
    
    fields = {
        "applicant": [applicant_id],  # Linked record
        "contractor_status": "Onboarding",
        **contractor_data
    }
    
    try:
        record = table.create(fields)
        record_id = record['id']
        
        logger.info(f"Created contractor record: {record_id}")
        log_airtable_update(
            table=TABLE_CONTRACTORS,
            record_id=record_id,
            fields_updated=fields,
            agent_name="hr_pipeline_agent"
        )
        
        return record_id
        
    except Exception as e:
        logger.error(f"Failed to create contractor: {str(e)}")
        raise


def get_contractor(record_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a contractor by record ID.
    
    Args:
        record_id: Airtable record ID
        
    Returns:
        Contractor record or None
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_CONTRACTORS)
    
    try:
        record = table.get(record_id)
        return {'id': record['id'], **record['fields']}
    except Exception as e:
        logger.error(f"Failed to get contractor {record_id}: {str(e)}")
        return None


def update_contractor(record_id: str, fields: Dict[str, Any]) -> bool:
    """
    Update a contractor record.
    
    Args:
        record_id: Airtable record ID
        fields: Fields to update
        
    Returns:
        True if successful
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_CONTRACTORS)
    
    try:
        # Get current values for audit
        current_record = table.get(record_id)
        before_values = {k: current_record['fields'].get(k) for k in fields.keys()}
        
        # Update record
        table.update(record_id, fields)
        
        logger.info(f"Updated contractor record: {record_id}")
        log_airtable_update(
            table=TABLE_CONTRACTORS,
            record_id=record_id,
            fields_updated=fields,
            agent_name="hr_pipeline_agent",
            before_values=before_values
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update contractor {record_id}: {str(e)}")
        return False

