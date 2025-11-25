"""
Pub/Sub tools for Google ADK agents.
"""
from typing import Dict, Any, Optional
from tools.pubsub.publisher import (
    publish_event,
    publish_airtable_event,
    publish_gmail_event,
    publish_drive_event,
    publish_chat_event
)


def pubsub_publish_event(topic_name: str, event_data: dict, attributes: Optional[dict] = None) -> str:
    """Publish an event to a Pub/Sub topic.
    
    Args:
        topic_name: Topic name (not full path)
        event_data: Event data dictionary (will be JSON encoded)
        attributes: Optional message attributes
        
    Returns:
        Message ID
    """
    return publish_event(topic_name, event_data, attributes)


def pubsub_publish_airtable(event_data: dict) -> str:
    """Publish an Airtable webhook event.
    
    Args:
        event_data: Event data dictionary
        
    Returns:
        Message ID
    """
    return publish_airtable_event(event_data)


def pubsub_publish_gmail(event_data: dict) -> str:
    """Publish a Gmail notification event.
    
    Args:
        event_data: Event data dictionary
        
    Returns:
        Message ID
    """
    return publish_gmail_event(event_data)


def pubsub_publish_drive(event_data: dict) -> str:
    """Publish a Drive file event.
    
    Args:
        event_data: Event data dictionary
        
    Returns:
        Message ID
    """
    return publish_drive_event(event_data)


def pubsub_publish_chat(event_data: dict) -> str:
    """Publish a Chat command event.
    
    Args:
        event_data: Event data dictionary
        
    Returns:
        Message ID
    """
    return publish_chat_event(event_data)


# Export all tools
ALL_PUBSUB_TOOLS = [
    pubsub_publish_event,
    pubsub_publish_airtable,
    pubsub_publish_gmail,
    pubsub_publish_drive,
    pubsub_publish_chat
]

