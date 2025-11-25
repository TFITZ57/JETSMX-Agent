"""
Airtable webhook routes.
"""
from fastapi import APIRouter, Request, HTTPException
from tools.pubsub.publisher import publish_airtable_event
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/applicant_pipeline")
async def airtable_pipeline_webhook(request: Request):
    """
    Receive Airtable webhook for Applicant Pipeline updates.
    """
    try:
        payload = await request.json()
        
        logger.info(f"Received Airtable webhook: {payload.get('table_id', 'unknown')}")
        
        # Publish to Pub/Sub for async processing
        message_id = publish_airtable_event(payload)
        
        logger.info(f"Published Airtable event to Pub/Sub: {message_id}")
        
        return {"status": "accepted", "message_id": message_id}
        
    except Exception as e:
        logger.error(f"Failed to process Airtable webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{table_name}")
async def airtable_generic_webhook(table_name: str, request: Request):
    """
    Generic Airtable webhook handler for any table.
    """
    try:
        payload = await request.json()
        payload['table_name'] = table_name
        
        logger.info(f"Received Airtable webhook for table: {table_name}")
        
        # Publish to Pub/Sub
        message_id = publish_airtable_event(payload)
        
        return {"status": "accepted", "message_id": message_id}
        
    except Exception as e:
        logger.error(f"Failed to process Airtable webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

