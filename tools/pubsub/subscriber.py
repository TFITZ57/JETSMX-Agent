"""
Pub/Sub subscription handlers.
"""
import json
from typing import Callable, Dict, Any
from concurrent import futures
from google.cloud.pubsub_v1.types import PubsubMessage
from tools.pubsub.client import get_pubsub_client
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def create_subscription(
    topic_name: str,
    subscription_name: str,
    push_endpoint: Optional[str] = None
) -> str:
    """
    Create a Pub/Sub subscription.
    
    Args:
        topic_name: Topic name
        subscription_name: Subscription name
        push_endpoint: Push endpoint URL (if None, creates pull subscription)
        
    Returns:
        Subscription path
    """
    client = get_pubsub_client()
    
    topic_path = client.publisher.topic_path(client.project_id, topic_name)
    subscription_path = client.subscriber.subscription_path(client.project_id, subscription_name)
    
    try:
        request = {
            'name': subscription_path,
            'topic': topic_path
        }
        
        if push_endpoint:
            request['push_config'] = {'push_endpoint': push_endpoint}
        
        subscription = client.subscriber.create_subscription(request=request)
        
        logger.info(f"Created subscription: {subscription_path}")
        return subscription_path
        
    except Exception as e:
        logger.error(f"Failed to create subscription: {str(e)}")
        raise


def subscribe_pull(
    subscription_name: str,
    callback: Callable[[Dict[str, Any]], None],
    max_messages: int = 10
) -> futures.Future:
    """
    Subscribe to a topic using pull delivery.
    
    Args:
        subscription_name: Subscription name
        callback: Callback function to handle messages
        max_messages: Max messages to process concurrently
        
    Returns:
        Streaming pull future
    """
    client = get_pubsub_client()
    
    subscription_path = client.subscriber.subscription_path(client.project_id, subscription_name)
    
    def message_handler(message: PubsubMessage):
        try:
            # Decode message data
            data = json.loads(message.data.decode('utf-8'))
            
            # Call callback with event data
            callback(data)
            
            # Acknowledge message
            message.ack()
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            message.nack()
    
    # Start streaming pull
    streaming_pull_future = client.subscriber.subscribe(
        subscription_path,
        callback=message_handler
    )
    
    logger.info(f"Subscribed to {subscription_path}")
    
    return streaming_pull_future


def acknowledge_message(subscription_name: str, ack_id: str) -> None:
    """
    Acknowledge a pulled message.
    
    Args:
        subscription_name: Subscription name
        ack_id: Acknowledgment ID
    """
    client = get_pubsub_client()
    
    subscription_path = client.subscriber.subscription_path(client.project_id, subscription_name)
    
    try:
        client.subscriber.acknowledge(
            request={'subscription': subscription_path, 'ack_ids': [ack_id]}
        )
        logger.debug(f"Acknowledged message: {ack_id}")
    except Exception as e:
        logger.error(f"Failed to acknowledge message: {str(e)}")

