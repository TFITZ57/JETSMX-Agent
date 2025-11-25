"""
Drive webhook routes (file change notifications).
"""
from fastapi import APIRouter, Request, HTTPException
from tools.pubsub.publisher import publish_drive_event
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("")
async def drive_notification(request: Request):
    """
    Receive Drive file change notifications.
    """
    try:
        # Get Drive notification headers
        channel_id = request.headers.get('X-Goog-Channel-ID')
        resource_id = request.headers.get('X-Goog-Resource-ID')
        resource_state = request.headers.get('X-Goog-Resource-State')
        
        logger.info(f"Drive notification: {resource_state} for channel {channel_id}")
        
        # For file added/updated events
        if resource_state in ['add', 'update', 'exists']:
            event_data = {
                'channel_id': channel_id,
                'resource_id': resource_id,
                'resource_state': resource_state
            }
            
            message_id = publish_drive_event(event_data)
            
            return {"status": "accepted", "message_id": message_id}
        
        return {"status": "ignored", "reason": f"Resource state {resource_state} not handled"}
        
    except Exception as e:
        logger.error(f"Failed to process Drive webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

