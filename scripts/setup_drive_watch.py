"""
Setup Drive folder watch for automatic resume processing.

This script configures Google Drive to send push notifications when files
are uploaded to the resumes folder.
"""
from tools.drive.folders import watch_folder
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def setup_drive_watch():
    """Set up Drive folder watch for resume uploads."""
    try:
        settings = get_settings()
        
        # Check required settings
        if not settings.drive_folder_resumes_incoming:
            logger.error("DRIVE_FOLDER_RESUMES_INCOMING not configured in .env")
            raise ValueError("DRIVE_FOLDER_RESUMES_INCOMING is required")
        
        if not settings.webhook_base_url:
            logger.error("WEBHOOK_BASE_URL not configured in .env")
            raise ValueError("WEBHOOK_BASE_URL is required")
        
        # Build webhook URL
        webhook_url = f"{settings.webhook_base_url}/webhooks/drive"
        folder_id = settings.drive_folder_resumes_incoming
        
        logger.info(f"Setting up watch on folder {folder_id}")
        logger.info(f"Webhook URL: {webhook_url}")
        
        # Setup watch
        watch_response = watch_folder(folder_id, webhook_url)
        
        if watch_response:
            logger.info("Drive watch configured successfully")
            logger.info(f"Channel ID: {watch_response.get('id')}")
            logger.info(f"Resource ID: {watch_response.get('resourceId')}")
            logger.info(f"Expiration: {watch_response.get('expiration')}")
            logger.info("Note: Drive watch may need to be renewed periodically")
            
            return watch_response
        else:
            logger.error("Failed to setup Drive watch")
            return None
        
    except Exception as e:
        logger.error(f"Failed to setup Drive watch: {str(e)}")
        raise


if __name__ == "__main__":
    setup_drive_watch()






