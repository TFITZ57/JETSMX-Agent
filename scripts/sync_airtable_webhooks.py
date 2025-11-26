#!/usr/bin/env python3
"""
Sync Airtable webhooks based on event_routing.yaml configuration.

Automatically creates webhook subscriptions for all tables referenced in routing rules.
Idempotent - safe to run multiple times.

Usage:
    python scripts/sync_airtable_webhooks.py [--dry-run] [--force]
    
    --dry-run: Show what would be created without making changes
    --force: Delete and recreate all webhooks (use with caution)
"""
import argparse
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.airtable.webhooks import AirtableWebhookClient, get_webhook_client
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def load_event_routing_config() -> Dict[str, Any]:
    """Load event routing configuration."""
    config_path = project_root / "SCHEMA" / "event_routing.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Event routing config not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def extract_tables_from_routing_config(config: Dict[str, Any]) -> Set[str]:
    """
    Extract unique table names from routing configuration.
    
    Args:
        config: Event routing YAML config
        
    Returns:
        Set of table names that need webhooks
    """
    tables = set()
    
    # Look through events for Airtable sources
    for event in config.get("events", []):
        if event.get("source") == "airtable":
            # Extract table from routing rules
            for rule in event.get("routing_rules", []):
                condition = rule.get("condition", "")
                
                # Parse table references from conditions
                # Examples: 'table_id == "applicant_pipeline"'
                if "table_id" in condition:
                    # Simple extraction - look for quoted table names
                    import re
                    matches = re.findall(r'table_id\s*==\s*["\']([^"\']+)["\']', condition)
                    tables.update(matches)
    
    # Also check table name from endpoint paths
    for event in config.get("events", []):
        endpoint = event.get("endpoint", "")
        if "/airtable/" in endpoint:
            # Extract table from path like /webhooks/airtable/applicant_pipeline
            parts = endpoint.split("/airtable/")
            if len(parts) > 1 and parts[1]:
                table_name = parts[1].strip("/")
                if table_name:
                    tables.add(table_name)
    
    # Add core tables explicitly (since they're always monitored)
    core_tables = {
        "applicant_pipeline",
        "applicants",
        "interactions",
        "contractors"
    }
    tables.update(core_tables)
    
    return tables


def create_webhook_specification(
    table_name: str,
    table_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create webhook specification for a table.
    
    Args:
        table_name: Table name
        table_id: Optional table ID (if known)
        
    Returns:
        Webhook specification dict
    """
    spec = {
        "options": {
            "filters": {
                "dataTypes": ["tableData"]
            }
        }
    }
    
    # If we have table ID, scope to that specific table
    if table_id:
        spec["options"]["filters"]["recordChangeScope"] = table_id
    
    return spec


def get_table_id_by_name(
    base_id: str,
    table_name: str,
    client: AirtableWebhookClient
) -> Optional[str]:
    """
    Get table ID by name using Airtable API.
    
    Note: This requires fetching base schema, which isn't in the webhooks API.
    For now, we'll create base-wide webhooks and filter in handlers.
    
    Args:
        base_id: Base ID
        table_name: Table name
        client: Webhook client
        
    Returns:
        Table ID or None
    """
    # TODO: Implement if we want table-specific webhooks
    # For now, return None to create base-wide webhooks
    return None


def sync_webhooks(
    dry_run: bool = False,
    force: bool = False
) -> None:
    """
    Sync Airtable webhooks based on configuration.
    
    Args:
        dry_run: If True, show what would be done without making changes
        force: If True, delete and recreate all webhooks
    """
    settings = get_settings()
    client = get_webhook_client()
    
    # Validate configuration
    if not settings.airtable_api_key:
        logger.error("AIRTABLE_API_KEY not set")
        sys.exit(1)
    
    if not settings.airtable_base_id:
        logger.error("AIRTABLE_BASE_ID not set")
        sys.exit(1)
    
    if not settings.webhook_base_url:
        logger.error("WEBHOOK_BASE_URL not set - deploy Cloud Run services first")
        sys.exit(1)
    
    base_id = settings.airtable_base_id
    notification_url = f"{settings.webhook_base_url}/webhooks/airtable"
    
    logger.info(f"Syncing webhooks for base: {base_id}")
    logger.info(f"Notification URL: {notification_url}")
    
    # Load configuration
    try:
        config = load_event_routing_config()
        tables = extract_tables_from_routing_config(config)
        logger.info(f"Found {len(tables)} tables in routing config: {', '.join(sorted(tables))}")
    except Exception as e:
        logger.error(f"Failed to load routing config: {str(e)}")
        sys.exit(1)
    
    # Get existing webhooks
    try:
        existing_webhooks = client.list_webhooks(base_id)
        logger.info(f"Found {len(existing_webhooks)} existing webhooks")
        
        for webhook in existing_webhooks:
            logger.info(f"  - {webhook['id']}: {webhook.get('notificationUrl', 'N/A')}")
    except Exception as e:
        logger.error(f"Failed to list webhooks: {str(e)}")
        sys.exit(1)
    
    # Delete existing webhooks if force mode
    if force:
        logger.warning("Force mode enabled - deleting all existing webhooks")
        
        for webhook in existing_webhooks:
            webhook_id = webhook['id']
            
            if dry_run:
                logger.info(f"[DRY RUN] Would delete webhook: {webhook_id}")
            else:
                try:
                    client.delete_webhook(base_id, webhook_id)
                    logger.info(f"Deleted webhook: {webhook_id}")
                except Exception as e:
                    logger.error(f"Failed to delete webhook {webhook_id}: {str(e)}")
        
        existing_webhooks = []
    
    # Check if we already have a webhook with our notification URL
    our_webhook = None
    for webhook in existing_webhooks:
        if webhook.get("notificationUrl") == notification_url:
            our_webhook = webhook
            break
    
    if our_webhook:
        logger.info(f"Webhook already exists: {our_webhook['id']}")
        logger.info(f"MAC Secret: {our_webhook.get('macSecretBase64', 'N/A')[:20]}...")
        
        # Check if notifications are enabled
        if our_webhook.get("isHookEnabled"):
            logger.info("Webhook notifications are enabled")
        else:
            logger.warning("Webhook notifications are disabled")
            
            if not dry_run:
                try:
                    client.enable_notifications(base_id, our_webhook['id'])
                    logger.info("Enabled webhook notifications")
                except Exception as e:
                    logger.error(f"Failed to enable notifications: {str(e)}")
        
        # Provide instructions to update env
        print("\n" + "="*60)
        print("WEBHOOK ALREADY EXISTS")
        print("="*60)
        print(f"Webhook ID: {our_webhook['id']}")
        print(f"MAC Secret: {our_webhook.get('macSecretBase64', 'N/A')}")
        print("\nAdd this to your .env file:")
        print(f"AIRTABLE_WEBHOOK_SECRET={our_webhook.get('macSecretBase64', 'N/A')}")
        print("="*60 + "\n")
        
    else:
        # Create new webhook
        logger.info("Creating new webhook subscription")
        
        # For now, create a base-wide webhook (watches all tables)
        # Alternative: create per-table webhooks if table IDs are known
        spec = create_webhook_specification("all_tables")
        
        if dry_run:
            logger.info(f"[DRY RUN] Would create webhook:")
            logger.info(f"  Base: {base_id}")
            logger.info(f"  URL: {notification_url}")
            logger.info(f"  Spec: {json.dumps(spec, indent=2)}")
        else:
            try:
                # Create webhook
                webhook = client.create_webhook(base_id, notification_url, spec)
                logger.info(f"Created webhook: {webhook['id']}")
                
                # Enable notifications
                webhook = client.enable_notifications(base_id, webhook['id'])
                logger.info("Enabled webhook notifications")
                
                # Print important info
                print("\n" + "="*60)
                print("WEBHOOK CREATED SUCCESSFULLY")
                print("="*60)
                print(f"Webhook ID: {webhook['id']}")
                print(f"MAC Secret: {webhook.get('macSecretBase64', 'N/A')}")
                print(f"Expiration: {webhook.get('expirationTime', 'N/A')}")
                print("\nIMPORTANT: Add this to your .env file:")
                print(f"AIRTABLE_WEBHOOK_SECRET={webhook.get('macSecretBase64', 'N/A')}")
                print("\nThe webhook will expire after 7 days of no activity.")
                print("Refresh it periodically using:")
                print(f"  python scripts/refresh_airtable_webhooks.py")
                print("="*60 + "\n")
                
            except Exception as e:
                logger.error(f"Failed to create webhook: {str(e)}")
                sys.exit(1)
    
    logger.info("Webhook sync complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sync Airtable webhooks based on event_routing.yaml"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete and recreate all webhooks (use with caution)"
    )
    
    args = parser.parse_args()
    
    if args.force and not args.dry_run:
        response = input("⚠️  Force mode will delete all webhooks. Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted")
            sys.exit(0)
    
    sync_webhooks(dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()







