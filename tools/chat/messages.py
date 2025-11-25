"""
Google Chat message operations.
"""
from typing import Optional, Dict, Any
from tools.chat.client import get_chat_client
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def post_message(space: str, text: str, thread_key: Optional[str] = None) -> dict:
    """
    Post a text message to a Chat space.
    
    Args:
        space: Space name (e.g., 'spaces/AAAA...')
        text: Message text
        thread_key: Thread key for replies
        
    Returns:
        Message info
    """
    client = get_chat_client()
    
    body = {'text': text}
    
    if thread_key:
        body['thread'] = {'threadKey': thread_key}
    
    try:
        message = client.service.spaces().messages().create(
            parent=space,
            body=body
        ).execute()
        
        logger.info(f"Posted message to {space}")
        return message
        
    except Exception as e:
        logger.error(f"Failed to post message: {str(e)}")
        raise


def post_card(space: str, card: Dict[str, Any], thread_key: Optional[str] = None) -> dict:
    """
    Post a card message to a Chat space.
    
    Args:
        space: Space name
        card: Card JSON structure
        thread_key: Thread key for replies
        
    Returns:
        Message info
    """
    client = get_chat_client()
    
    body = {
        'cardsV2': [{
            'cardId': 'jetsmx-card',
            'card': card
        }]
    }
    
    if thread_key:
        body['thread'] = {'threadKey': thread_key}
    
    try:
        message = client.service.spaces().messages().create(
            parent=space,
            body=body
        ).execute()
        
        logger.info(f"Posted card to {space}")
        return message
        
    except Exception as e:
        logger.error(f"Failed to post card: {str(e)}")
        raise


def update_message(message_name: str, text: Optional[str] = None, card: Optional[Dict[str, Any]] = None) -> dict:
    """
    Update an existing message.
    
    Args:
        message_name: Full message name (e.g., 'spaces/AAAA/messages/BBBB')
        text: New text (if updating text message)
        card: New card (if updating card message)
        
    Returns:
        Updated message info
    """
    client = get_chat_client()
    
    body = {}
    
    if text:
        body['text'] = text
    
    if card:
        body['cardsV2'] = [{
            'cardId': 'jetsmx-card',
            'card': card
        }]
    
    try:
        message = client.service.spaces().messages().update(
            name=message_name,
            body=body,
            updateMask='text,cardsV2' if card else 'text'
        ).execute()
        
        logger.info(f"Updated message {message_name}")
        return message
        
    except Exception as e:
        logger.error(f"Failed to update message: {str(e)}")
        raise


def delete_message(message_name: str) -> bool:
    """
    Delete a message.
    
    Args:
        message_name: Full message name
        
    Returns:
        True if successful
    """
    client = get_chat_client()
    
    try:
        client.service.spaces().messages().delete(name=message_name).execute()
        logger.info(f"Deleted message {message_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete message: {str(e)}")
        return False

