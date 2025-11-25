"""
Gmail webhook routes (push notifications).
"""
import base64
import json
from fastapi import APIRouter, Request, HTTPException
from tools.pubsub.publisher import publish_gmail_event
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("")
async def gmail_push_notification(request: Request):
    """
    Receive Gmail push notifications via Pub/Sub.
    """
    try:
        payload = await request.json()
        
        # Decode Pub/Sub message
        if 'message' in payload:
            message = payload['message']
            data = base64.b64decode(message['data']).decode('utf-8')
            history_id = json.loads(data).get('historyId')
            
            logger.info(f"Received Gmail push notification: history ID {history_id}")
            
            # Publish to internal Pub/Sub for processing
            event_data = {
                'history_id': history_id,
                'email_address': json.loads(data).get('emailAddress')
            }
            
            message_id = publish_gmail_event(event_data)
            
            return {"status": "accepted", "message_id": message_id}
        
        return {"status": "ignored", "reason": "No message in payload"}
        
    except Exception as e:
        logger.error(f"Failed to process Gmail webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

