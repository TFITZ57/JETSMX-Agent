"""
Pub/Sub publishing helpers.
"""
import json
from typing import Dict, Any, Optional
from tools.pubsub.client import get_pubsub_client
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def publish_event(topic_name: str, event_data: Dict[str, Any], attributes: Optional[Dict[str, str]] = None) -> str:
    """
    Publish an event to a Pub/Sub topic.
    
    Args:
        topic_name: Topic name (not full path, just the name)
        event_data: Event data to publish (will be JSON encoded)
        attributes: Optional message attributes
        
    Returns:
        Message ID
    """
    client = get_pubsub_client()
    
    # Build full topic path
    topic_path = client.publisher.topic_path(client.project_id, topic_name)
    
    # Encode event data as JSON bytes
    data = json.dumps(event_data).encode('utf-8')
    
    try:
        # Publish message
        future = client.publisher.publish(
            topic_path,
            data,
            **(attributes or {})
        )
        
        # Wait for message ID
        message_id = future.result()
        
        logger.info(f"Published event to {topic_name}: {message_id}")
        return message_id
        
    except Exception as e:
        logger.error(f"Failed to publish to {topic_name}: {str(e)}")
        raise


def publish_airtable_event(event_data: Dict[str, Any]) -> str:
    """Publish an Airtable webhook event."""
    from shared.config.settings import get_settings
    settings = get_settings()
    return publish_event(settings.pubsub_topic_airtable, event_data)


def publish_gmail_event(event_data: Dict[str, Any]) -> str:
    """Publish a Gmail notification event."""
    from shared.config.settings import get_settings
    settings = get_settings()
    return publish_event(settings.pubsub_topic_gmail, event_data)


def publish_drive_event(event_data: Dict[str, Any]) -> str:
    """Publish a Drive file event."""
    from shared.config.settings import get_settings
    settings = get_settings()
    return publish_event(settings.pubsub_topic_drive, event_data)


def publish_chat_event(event_data: Dict[str, Any]) -> str:
    """Publish a Chat command event."""
    from shared.config.settings import get_settings
    settings = get_settings()
    return publish_event(settings.pubsub_topic_chat, event_data)

