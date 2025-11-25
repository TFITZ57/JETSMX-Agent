"""
Setup Pub/Sub topics and subscriptions for JetsMX Agent.
"""
from google.cloud import pubsub_v1
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


def create_topics():
    """Create Pub/Sub topics."""
    publisher = pubsub_v1.PublisherClient()
    project_id = settings.gcp_project_id
    
    topics = [
        settings.pubsub_topic_airtable,
        settings.pubsub_topic_gmail,
        settings.pubsub_topic_drive,
        settings.pubsub_topic_chat
    ]
    
    for topic_name in topics:
        topic_path = publisher.topic_path(project_id, topic_name)
        
        try:
            topic = publisher.create_topic(request={"name": topic_path})
            logger.info(f"Created topic: {topic.name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"Topic already exists: {topic_path}")
            else:
                logger.error(f"Failed to create topic {topic_name}: {str(e)}")
                raise


def create_subscriptions():
    """Create Pub/Sub subscriptions with push endpoints."""
    subscriber = pubsub_v1.SubscriberClient()
    project_id = settings.gcp_project_id
    
    # These would be the Cloud Run service URLs
    # In production, you'd get these from deployment or config
    base_url = "https://pubsub-handler-XXXXX-uc.a.run.app"  # Replace with actual URL
    
    subscriptions = [
        {
            'name': f"{settings.pubsub_topic_airtable}-sub",
            'topic': settings.pubsub_topic_airtable,
            'push_endpoint': f"{base_url}/pubsub/airtable"
        },
        {
            'name': f"{settings.pubsub_topic_gmail}-sub",
            'topic': settings.pubsub_topic_gmail,
            'push_endpoint': f"{base_url}/pubsub/gmail"
        },
        {
            'name': f"{settings.pubsub_topic_drive}-sub",
            'topic': settings.pubsub_topic_drive,
            'push_endpoint': f"{base_url}/pubsub/drive"
        },
        {
            'name': f"{settings.pubsub_topic_chat}-sub",
            'topic': settings.pubsub_topic_chat,
            'push_endpoint': f"{base_url}/pubsub/chat"
        }
    ]
    
    for sub_config in subscriptions:
        sub_name = sub_config['name']
        topic_name = sub_config['topic']
        push_endpoint = sub_config['push_endpoint']
        
        subscription_path = subscriber.subscription_path(project_id, sub_name)
        topic_path = subscriber.topic_path(project_id, topic_name)
        
        try:
            subscription = subscriber.create_subscription(
                request={
                    "name": subscription_path,
                    "topic": topic_path,
                    "push_config": {"push_endpoint": push_endpoint}
                }
            )
            logger.info(f"Created subscription: {subscription.name}")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"Subscription already exists: {subscription_path}")
            else:
                logger.error(f"Failed to create subscription {sub_name}: {str(e)}")
                raise


if __name__ == "__main__":
    logger.info("Setting up Pub/Sub topics and subscriptions...")
    
    try:
        create_topics()
        logger.info("Topics created successfully")
        
        # Note: Subscriptions should be created after Cloud Run services are deployed
        # Uncomment when you have the Cloud Run URLs
        # create_subscriptions()
        # logger.info("Subscriptions created successfully")
        
        logger.info("Pub/Sub setup complete!")
        
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}")
        raise

