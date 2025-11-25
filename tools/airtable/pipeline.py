"""
Applicant Pipeline table operations.
"""
from typing import Optional, List
from tools.airtable.client import get_airtable_client
from shared.config.constants import TABLE_APPLICANT_PIPELINE
from shared.models.pipeline import PipelineCreate, PipelineUpdate, Pipeline
from shared.logging.logger import setup_logger
from shared.logging.audit import log_airtable_update

logger = setup_logger(__name__)


def create_pipeline_record(
    data: PipelineCreate,
    initiated_by: str,
    reason: str
) -> str:
    """
    Create a new pipeline record.
    
    Args:
        data: Pipeline data
        initiated_by: Who is initiating this creation (agent name or user email)
        reason: Explicit reason for creating this pipeline record
        
    Returns:
        Record ID
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_APPLICANT_PIPELINE)
    
    # Convert model to dict and filter None values
    fields = {k: v for k, v in data.model_dump().items() if v is not None}
    
    try:
        record = table.create(fields)
        record_id = record['id']
        
        logger.info(f"Created pipeline record: {record_id}")
        log_airtable_update(
            table=TABLE_APPLICANT_PIPELINE,
            record_id=record_id,
            fields_updated=fields,
            initiated_by=initiated_by,
            reason=reason
        )
        
        return record_id
        
    except Exception as e:
        logger.error(f"Failed to create pipeline record: {str(e)}")
        raise


def get_pipeline_record(record_id: str) -> Optional[Pipeline]:
    """
    Get a pipeline record by ID.
    
    Args:
        record_id: Airtable record ID
        
    Returns:
        Pipeline or None
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_APPLICANT_PIPELINE)
    
    try:
        record = table.get(record_id)
        
        # Convert Airtable list to first element for linked records
        fields = record['fields'].copy()
        if 'applicant' in fields and isinstance(fields['applicant'], list):
            fields['applicant'] = fields['applicant'][0]
        
        pipeline = Pipeline(id=record['id'], **fields)
        return pipeline
    except Exception as e:
        logger.error(f"Failed to get pipeline record {record_id}: {str(e)}")
        return None


def update_pipeline_record(
    record_id: str,
    data: PipelineUpdate,
    initiated_by: str,
    reason: str
) -> bool:
    """
    Update a pipeline record.
    
    Args:
        record_id: Airtable record ID
        data: Fields to update
        initiated_by: Who is initiating this update (agent name or user email)
        reason: Explicit reason for updating this pipeline record
        
    Returns:
        True if successful
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_APPLICANT_PIPELINE)
    
    # Convert model to dict and filter None values
    fields = {k: v for k, v in data.model_dump().items() if v is not None}
    
    # Convert datetime objects to ISO strings
    for key, value in fields.items():
        if hasattr(value, 'isoformat'):
            fields[key] = value.isoformat()
    
    if not fields:
        logger.warning("No fields to update")
        return False
    
    try:
        # Get current values for audit
        current_record = table.get(record_id)
        before_values = {k: current_record['fields'].get(k) for k in fields.keys()}
        
        # Update record
        table.update(record_id, fields)
        
        logger.info(f"Updated pipeline record: {record_id}")
        log_airtable_update(
            table=TABLE_APPLICANT_PIPELINE,
            record_id=record_id,
            fields_updated=fields,
            initiated_by=initiated_by,
            reason=reason,
            before_values=before_values
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to update pipeline record {record_id}: {str(e)}")
        return False


def find_pipeline_by_thread_id(thread_id: str) -> Optional[Pipeline]:
    """
    Find pipeline record by Gmail thread ID.
    
    Args:
        thread_id: Gmail thread ID
        
    Returns:
        Pipeline or None
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_APPLICANT_PIPELINE)
    
    formula = f"{{outreach_thread_id}} = '{thread_id}'"
    
    try:
        records = table.all(formula=formula)
        if records:
            record = records[0]
            fields = record['fields'].copy()
            if 'applicant' in fields and isinstance(fields['applicant'], list):
                fields['applicant'] = fields['applicant'][0]
            return Pipeline(id=record['id'], **fields)
        return None
    except Exception as e:
        logger.error(f"Failed to find pipeline by thread {thread_id}: {str(e)}")
        return None


def find_pipeline_records(formula: Optional[str] = None, view: Optional[str] = None) -> List[Pipeline]:
    """
    Find pipeline records matching criteria.
    
    Args:
        formula: Airtable formula
        view: View name to use
        
    Returns:
        List of pipeline records
    """
    client = get_airtable_client()
    table = client.get_table(TABLE_APPLICANT_PIPELINE)
    
    try:
        records = table.all(formula=formula, view=view)
        pipelines = []
        for r in records:
            fields = r['fields'].copy()
            if 'applicant' in fields and isinstance(fields['applicant'], list):
                fields['applicant'] = fields['applicant'][0]
            pipelines.append(Pipeline(id=r['id'], **fields))
        return pipelines
    except Exception as e:
        logger.error(f"Failed to find pipeline records: {str(e)}")
        return []

