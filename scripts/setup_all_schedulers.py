#!/usr/bin/env python3
"""
Setup all Cloud Scheduler jobs for automated maintenance tasks.

This script creates/updates:
1. Gmail watch renewal (every 6 days)
2. Airtable webhook refresh (every 5 days)
"""
import sys
from setup_gmail_watch_scheduler import create_gmail_watch_scheduler
from setup_airtable_webhook_scheduler import create_airtable_webhook_scheduler
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


def setup_all_schedulers(
    webhook_service_url: str,
    service_account_email: str
):
    """
    Setup all automated scheduler jobs.
    
    Args:
        webhook_service_url: Cloud Run service URL
        service_account_email: Service account email for OIDC auth
    """
    results = []
    
    # Setup Gmail watch renewal
    try:
        logger.info("Setting up Gmail watch renewal scheduler...")
        gmail_job = create_gmail_watch_scheduler(webhook_service_url, service_account_email)
        results.append({
            "name": "Gmail Watch Renewal",
            "job": gmail_job,
            "status": "success"
        })
        print("✅ Gmail watch renewal scheduler configured")
    except Exception as e:
        logger.error(f"Failed to setup Gmail watch scheduler: {str(e)}")
        results.append({
            "name": "Gmail Watch Renewal",
            "status": "failed",
            "error": str(e)
        })
        print(f"❌ Gmail watch renewal scheduler failed: {str(e)}")
    
    # Setup Airtable webhook refresh
    try:
        logger.info("Setting up Airtable webhook refresh scheduler...")
        airtable_job = create_airtable_webhook_scheduler(webhook_service_url, service_account_email)
        results.append({
            "name": "Airtable Webhook Refresh",
            "job": airtable_job,
            "status": "success"
        })
        print("✅ Airtable webhook refresh scheduler configured")
    except Exception as e:
        logger.error(f"Failed to setup Airtable webhook scheduler: {str(e)}")
        results.append({
            "name": "Airtable Webhook Refresh",
            "status": "failed",
            "error": str(e)
        })
        print(f"❌ Airtable webhook refresh scheduler failed: {str(e)}")
    
    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/setup_all_schedulers.py <webhook_service_url> <service_account_email>")
        print()
        print("Example:")
        print("  python scripts/setup_all_schedulers.py \\")
        print("    https://jetsmx-webhooks-wg3iuj477q-uc.a.run.app \\")
        print("    jetsmx-agent@jetsmx-agent.iam.gserviceaccount.com")
        print()
        print("To get your Cloud Run service URL:")
        print("  gcloud run services describe jetsmx-webhooks --region us-central1 --format='value(status.url)'")
        print()
        print("To get your service account email:")
        print("  gcloud iam service-accounts list --filter='NAME:jetsmx-agent'")
        sys.exit(1)
    
    webhook_url = sys.argv[1].rstrip('/')
    service_account = sys.argv[2]
    
    print("="*70)
    print("Setting up Cloud Scheduler Jobs")
    print("="*70)
    print(f"Webhook URL: {webhook_url}")
    print(f"Service Account: {service_account}")
    print()
    
    results = setup_all_schedulers(webhook_url, service_account)
    
    print()
    print("="*70)
    print("Setup Summary")
    print("="*70)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    
    for result in results:
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {result['name']}: {result['status']}")
        if result["status"] == "success" and "job" in result:
            print(f"   Schedule: {result['job'].schedule}")
        elif "error" in result:
            print(f"   Error: {result['error']}")
    
    print()
    print(f"Total: {success_count} succeeded, {failed_count} failed")
    
    if success_count > 0:
        print()
        print("To view all scheduler jobs:")
        print("  gcloud scheduler jobs list --location=us-central1")
        print()
        print("To manually trigger a job:")
        print("  gcloud scheduler jobs run gmail-watch-renewal --location=us-central1")
        print("  gcloud scheduler jobs run airtable-webhook-refresh --location=us-central1")
    
    sys.exit(0 if failed_count == 0 else 1)







