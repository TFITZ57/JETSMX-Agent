#!/usr/bin/env python3
"""
Refresh Airtable webhooks to extend expiration time.

Webhooks expire after 7 days of no activity. Run this periodically to keep them alive.

Usage:
    python scripts/refresh_airtable_webhooks.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.airtable.webhooks import get_webhook_client
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def refresh_webhooks():
    """Refresh all webhooks for the configured base."""
    settings = get_settings()
    client = get_webhook_client()
    
    if not settings.airtable_base_id:
        logger.error("AIRTABLE_BASE_ID not set")
        sys.exit(1)
    
    base_id = settings.airtable_base_id
    
    logger.info(f"Refreshing webhooks for base: {base_id}")
    
    try:
        # List all webhooks
        webhooks = client.list_webhooks(base_id)
        logger.info(f"Found {len(webhooks)} webhooks")
        
        if not webhooks:
            logger.warning("No webhooks found to refresh")
            return
        
        # Refresh each webhook
        for webhook in webhooks:
            webhook_id = webhook['id']
            old_expiration = webhook.get('expirationTime', 'unknown')
            
            try:
                refreshed = client.refresh_webhook(base_id, webhook_id)
                new_expiration = refreshed.get('expirationTime', 'unknown')
                
                logger.info(
                    f"Refreshed webhook {webhook_id}",
                    extra={"extra_fields": {
                        "webhook_id": webhook_id,
                        "old_expiration": old_expiration,
                        "new_expiration": new_expiration
                    }}
                )
                
                print(f"✓ Refreshed {webhook_id}")
                print(f"  Old expiration: {old_expiration}")
                print(f"  New expiration: {new_expiration}")
                print()
                
            except Exception as e:
                logger.error(f"Failed to refresh webhook {webhook_id}: {str(e)}")
                print(f"✗ Failed to refresh {webhook_id}: {str(e)}")
        
        logger.info("Webhook refresh complete")
        
    except Exception as e:
        logger.error(f"Failed to refresh webhooks: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point."""
    refresh_webhooks()


if __name__ == "__main__":
    main()







