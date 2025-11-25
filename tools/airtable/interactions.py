"""
Interactions table operations for logging applicant touchpoints.
"""
from typing import Optional, List
from datetime import datetime
from tools.airtable.client import get_airtable_client
from shared.config.constants import TABLE_INTERACTIONS
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def log_interaction(
    applicant_id: str,
    interaction_type: str,
    direction: str,
    channel: str,
    summary: str,
    created_by: str = "JetsMX AGENT",
    source_reference: Optional[str] = None,
    timestamp: Optional[datetime] = None
) -> str:
    """
    Log an interaction with an applicant.
    
    Args:
        applicant_id: Airtable applicant record ID
        interaction_type: Type (System, Email, Phone Call, Video Interview, Chat Note)
        direction: Inbound, Outbound, or System
        channel: Gmail, Calendar, Drive, Chat, or Manual
        summary: Text summary of the interaction
        created_by: Who created the interaction
        source_reference: External reference (e.g., message ID)
        timestamp: When the interaction occurred
        
    Returns:
        Record ID
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_INTERACTIONS)
    
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    fields = {
        "applicant": [applicant_id],  # Linked record field
        "interaction_type": interaction_type,
        "direction": direction,
        "channel": channel,
        "summary": summary,
        "created_by": created_by,
        "timestamp": timestamp.isoformat()
    }
    
    if source_reference:
        fields["source_reference"] = source_reference
    
    try:
        record = table.create(fields)
        record_id = record['id']
        logger.info(f"Logged interaction: {record_id} for applicant {applicant_id}")
        return record_id
    except Exception as e:
        logger.error(f"Failed to log interaction: {str(e)}")
        raise


def get_applicant_interactions(applicant_id: str) -> List[dict]:
    """
    Get all interactions for an applicant.
    
    Args:
        applicant_id: Airtable applicant record ID
        
    Returns:
        List of interaction records
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_INTERACTIONS)
    
    # Note: This uses a formula to find linked records
    formula = f"FIND('{applicant_id}', {{applicant}})"
    
    try:
        records = table.all(formula=formula, sort=['-timestamp'])
        return [{'id': r['id'], **r['fields']} for r in records]
    except Exception as e:
        logger.error(f"Failed to get interactions for {applicant_id}: {str(e)}")
        return []

