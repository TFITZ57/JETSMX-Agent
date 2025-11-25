"""
Setup Gmail push notifications via Pub/Sub.
"""
from tools.gmail.watch import setup_watch
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


def setup_gmail_notifications():
    """Set up Gmail push notifications."""
    try:
        logger.info(f"Setting up Gmail watch for {settings.gmail_user_email}")
        
        watch_response = setup_watch(
            label_ids=['INBOX'],  # Watch inbox for new messages
            topic_name=settings.gmail_watch_topic
        )
        
        logger.info(f"Gmail watch configured successfully")
        logger.info(f"History ID: {watch_response.get('historyId')}")
        logger.info(f"Expiration: {watch_response.get('expiration')}")
        logger.info("Note: Gmail watch expires after 7 days and must be renewed")
        
        return watch_response
        
    except Exception as e:
        logger.error(f"Failed to setup Gmail watch: {str(e)}")
        raise


if __name__ == "__main__":
    setup_gmail_notifications()

