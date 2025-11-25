"""
Airtable webhook routes.

Receives webhooks from Airtable Web API and dispatches to appropriate handlers.
"""
from fastapi import APIRouter, Request, HTTPException
from infra.webhooks.handlers import (
    ApplicantPipelineHandler,
    ApplicantsHandler,
    InteractionsHandler,
    ContractorsHandler
)
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# Initialize handlers
HANDLERS = {
    "applicant_pipeline": ApplicantPipelineHandler(),
    "applicants": ApplicantsHandler(),
    "interactions": InteractionsHandler(),
    "contractors": ContractorsHandler(),
}


@router.post("/")
async def airtable_webhook(request: Request):
    """
    Universal Airtable webhook receiver.
    
    Receives webhooks from Airtable Web API and routes to appropriate handler
    based on which table(s) changed.
    
    Payload structure:
    {
        "baseId": "appXXX",
        "webhookId": "achXXX",
        "timestamp": "2025-11-25T...",
        "baseTransactionNumber": 123,
        "changedTablesById": {
            "tblXXX": {
                "name": "applicant_pipeline",
                "changedRecordsById": {...},
                "createdRecordsById": {...},
                "destroyedRecordIds": [...]
            }
        }
    }
    """
    try:
        payload = await request.json()
        
        webhook_id = payload.get("webhookId", "unknown")
        base_id = payload.get("baseId", "unknown")
        
        logger.info(
            f"Received Airtable webhook: {webhook_id}",
            extra={"extra_fields": {
                "webhook_id": webhook_id,
                "base_id": base_id,
                "timestamp": payload.get("timestamp")
            }}
        )
        
        # Extract changed tables
        changed_tables = payload.get("changedTablesById", {})
        
        if not changed_tables:
            logger.warning("Webhook has no changed tables")
            return {"status": "ignored", "reason": "no_changes"}
        
        # Process each changed table
        results = []
        for table_id, table_data in changed_tables.items():
            table_name = table_data.get("name", "unknown")
            
            logger.info(f"Processing changes for table: {table_name} ({table_id})")
            
            # Find appropriate handler
            handler = HANDLERS.get(table_name)
            
            if handler:
                try:
                    result = await handler.handle(payload)
                    results.append({
                        "table": table_name,
                        "table_id": table_id,
                        "result": result
                    })
                except Exception as e:
                    logger.error(f"Handler failed for {table_name}: {str(e)}", exc_info=True)
                    results.append({
                        "table": table_name,
                        "table_id": table_id,
                        "error": str(e)
                    })
            else:
                logger.warning(f"No handler registered for table: {table_name}")
                results.append({
                    "table": table_name,
                    "table_id": table_id,
                    "status": "no_handler"
                })
        
        return {
            "status": "processed",
            "webhook_id": webhook_id,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to process Airtable webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{table_name}")
async def airtable_legacy_webhook(table_name: str, request: Request):
    """
    Legacy webhook endpoint for backwards compatibility.
    
    Kept for any existing manual webhook configurations.
    Transforms the payload to match Airtable API format and dispatches.
    """
    try:
        payload = await request.json()
        
        logger.info(f"Received legacy webhook for table: {table_name}")
        
        # If it's already in Airtable format, use main handler
        if "changedTablesById" in payload:
            return await airtable_webhook(request)
        
        # Otherwise, find handler and process directly
        handler = HANDLERS.get(table_name)
        
        if not handler:
            logger.warning(f"No handler for table: {table_name}")
            return {"status": "no_handler", "table": table_name}
        
        # Transform to expected format
        wrapped_payload = {
            "baseId": payload.get("base_id", "unknown"),
            "webhookId": "legacy",
            "timestamp": payload.get("timestamp"),
            "changedTablesById": {
                payload.get("table_id", "unknown"): {
                    "name": table_name,
                    "changedRecordsById": {},
                    "createdRecordsById": {}
                }
            }
        }
        
        result = await handler.handle(wrapped_payload)
        
        return {
            "status": "processed",
            "table": table_name,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to process legacy webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

