"""
Google Chat webhook routes (commands and interactions).
"""
from fastapi import APIRouter, Request, HTTPException
from tools.pubsub.publisher import publish_chat_event
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/command")
async def chat_command(request: Request):
    """
    Receive Google Chat slash commands.
    """
    try:
        payload = await request.json()
        
        # Extract command from Chat payload
        message = payload.get('message', {})
        space = payload.get('space', {}).get('name')
        user = payload.get('user', {}).get('name')
        text = message.get('text', '')
        
        logger.info(f"Received Chat command from {user}: {text}")
        
        # Parse command
        if text.startswith('/'):
            parts = text.split(' ', 1)
            command = parts[0]
            args = parts[1] if len(parts) > 1 else ''
            
            event_data = {
                'space': space,
                'user': user,
                'command': command,
                'args': args,
                'timestamp': message.get('createTime')
            }
            
            message_id = publish_chat_event(event_data)
            
            return {
                "text": f"Processing command: {command}..."
            }
        
        return {"text": "No command recognized"}
        
    except Exception as e:
        logger.error(f"Failed to process Chat command: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interaction")
async def chat_interaction(request: Request):
    """
    Receive Google Chat card button interactions.
    """
    try:
        payload = await request.json()
        
        # Extract interaction data
        action = payload.get('action', {})
        action_name = action.get('actionMethodName')
        parameters = action.get('parameters', [])
        
        logger.info(f"Received Chat interaction: {action_name}")
        
        # Convert parameters to dict
        params_dict = {p['key']: p['value'] for p in parameters}
        
        event_data = {
            'action_name': action_name,
            'parameters': params_dict,
            'space': payload.get('space', {}).get('name'),
            'user': payload.get('user', {}).get('name')
        }
        
        message_id = publish_chat_event(event_data)
        
        return {
            "text": "Processing your action..."
        }
        
    except Exception as e:
        logger.error(f"Failed to process Chat interaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

