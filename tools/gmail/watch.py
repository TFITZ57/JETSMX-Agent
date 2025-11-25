"""
Gmail watch/push notification setup.
"""
from typing import Optional, List
from tools.gmail.client import get_gmail_client
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def setup_watch(label_ids: Optional[List[str]] = None, topic_name: Optional[str] = None) -> dict:
    """
    Set up Gmail push notifications via Pub/Sub.
    
    Args:
        label_ids: Labels to watch (None = all mail)
        topic_name: Pub/Sub topic name (uses settings if not provided)
        
    Returns:
        Watch response with historyId and expiration
    """
    client = get_gmail_client()
    settings = get_settings()
    
    if topic_name is None:
        topic_name = settings.gmail_watch_topic
    
    request_body = {
        'topicName': topic_name
    }
    
    if label_ids:
        request_body['labelIds'] = label_ids
    
    try:
        watch_response = client.service.users().watch(
            userId='me',
            body=request_body
        ).execute()
        
        logger.info(f"Gmail watch set up for topic {topic_name}")
        logger.info(f"History ID: {watch_response.get('historyId')}, Expires: {watch_response.get('expiration')}")
        
        return watch_response
        
    except Exception as e:
        logger.error(f"Failed to set up Gmail watch: {str(e)}")
        raise


def stop_watch() -> bool:
    """
    Stop Gmail push notifications.
    
    Returns:
        True if successful
    """
    client = get_gmail_client()
    
    try:
        client.service.users().stop(userId='me').execute()
        logger.info("Gmail watch stopped")
        return True
    except Exception as e:
        logger.error(f"Failed to stop Gmail watch: {str(e)}")
        return False


def get_history(start_history_id: str, max_results: int = 100) -> List[dict]:
    """
    Get Gmail history since a history ID.
    
    Args:
        start_history_id: Starting history ID
        max_results: Maximum results to return
        
    Returns:
        List of history records
    """
    client = get_gmail_client()
    
    try:
        results = client.service.users().history().list(
            userId='me',
            startHistoryId=start_history_id,
            maxResults=max_results
        ).execute()
        
        history = results.get('history', [])
        logger.info(f"Retrieved {len(history)} history records")
        return history
        
    except Exception as e:
        logger.error(f"Failed to get history: {str(e)}")
        return []

