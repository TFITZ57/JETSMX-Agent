"""
Internal scheduler routes for automated tasks.
"""
from fastapi import APIRouter, HTTPException
from tools.gmail.watch import setup_watch
from tools.airtable.webhooks import get_webhook_client
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/renew-gmail-watch")
async def renew_gmail_watch():
    """
    Renew Gmail watch subscription.
    
    This endpoint is called by Cloud Scheduler every 6 days to automatically
    renew the Gmail push notification watch before it expires (7 day limit).
    
    Returns:
        dict: Status and watch details including expiration timestamp
    """
    try:
        logger.info("Starting automated Gmail watch renewal")
        
        # Call the existing setup_watch function
        watch_response = setup_watch(
            label_ids=['INBOX'],
            topic_name=settings.gmail_watch_topic
        )
        
        history_id = watch_response.get('historyId')
        expiration = watch_response.get('expiration')
        
        logger.info(
            f"Gmail watch renewed successfully - History ID: {history_id}, Expiration: {expiration}",
            extra={"extra_fields": {
                "history_id": history_id,
                "expiration": expiration
            }}
        )
        
        return {
            "status": "success",
            "message": "Gmail watch renewed successfully",
            "history_id": history_id,
            "expiration": expiration
        }
        
    except Exception as e:
        logger.error(
            f"Failed to renew Gmail watch: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"error": str(e)}}
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to renew Gmail watch: {str(e)}"
        )


@router.post("/refresh-airtable-webhooks")
async def refresh_airtable_webhooks():
    """
    Refresh Airtable webhook subscriptions.
    
    This endpoint is called by Cloud Scheduler every 5 days to automatically
    refresh Airtable webhooks before they expire (7 day limit).
    
    Returns:
        dict: Status and refreshed webhook details
    """
    try:
        logger.info("Starting automated Airtable webhook refresh")
        
        client = get_webhook_client()
        webhooks = client.list_webhooks(settings.airtable_base_id)
        
        if not webhooks:
            logger.warning("No Airtable webhooks found to refresh")
            return {
                "status": "success",
                "message": "No webhooks to refresh",
                "webhooks_refreshed": 0
            }
        
        refreshed_webhooks = []
        for webhook in webhooks:
            webhook_id = webhook['id']
            old_expiration = webhook.get('expirationTime')
            
            logger.info(f"Refreshing webhook {webhook_id}")
            
            # Refresh webhook (returns updated webhook with new expiration)
            updated_webhook = client.refresh_webhook(settings.airtable_base_id, webhook_id)
            new_expiration = updated_webhook.get('expirationTime')
            
            refreshed_webhooks.append({
                "webhook_id": webhook_id,
                "old_expiration": old_expiration,
                "new_expiration": new_expiration
            })
            
            logger.info(
                f"Webhook {webhook_id} refreshed - New expiration: {new_expiration}",
                extra={"extra_fields": {
                    "webhook_id": webhook_id,
                    "old_expiration": old_expiration,
                    "new_expiration": new_expiration
                }}
            )
        
        return {
            "status": "success",
            "message": f"Refreshed {len(refreshed_webhooks)} Airtable webhooks",
            "webhooks_refreshed": len(refreshed_webhooks),
            "webhooks": refreshed_webhooks
        }
        
    except Exception as e:
        logger.error(
            f"Failed to refresh Airtable webhooks: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"error": str(e)}}
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh Airtable webhooks: {str(e)}"
        )

