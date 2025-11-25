"""
Internal scheduler routes for automated tasks.
"""
from fastapi import APIRouter, HTTPException
from tools.gmail.watch import setup_watch
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

