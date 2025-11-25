"""
Setup Cloud Scheduler job to automatically renew Gmail watch every 6 days.
"""
from google.cloud import scheduler_v1
from google.protobuf import duration_pb2
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


def create_gmail_watch_scheduler(
    webhook_service_url: str,
    service_account_email: str
) -> scheduler_v1.Job:
    """
    Create Cloud Scheduler job to renew Gmail watch every 6 days.
    
    Args:
        webhook_service_url: Cloud Run service URL (e.g., https://jetsmx-webhooks-xxx.run.app)
        service_account_email: Service account email for OIDC auth
        
    Returns:
        Created scheduler job
    """
    client = scheduler_v1.CloudSchedulerClient()
    
    # Job configuration
    project_id = settings.gcp_project_id
    location = "us-central1"  # Cloud Scheduler location
    job_name = "gmail-watch-renewal"
    
    parent = f"projects/{project_id}/locations/{location}"
    full_job_name = f"{parent}/jobs/{job_name}"
    
    # Check if job already exists
    try:
        existing_job = client.get_job(name=full_job_name)
        logger.info(f"Cloud Scheduler job '{job_name}' already exists")
        
        # Update the existing job
        job = scheduler_v1.Job(
            name=full_job_name,
            description="Automatically renew Gmail watch subscription every 6 days",
            schedule="0 0 */6 * *",  # Every 6 days at midnight UTC
            time_zone="UTC",
            http_target=scheduler_v1.HttpTarget(
                uri=f"{webhook_service_url}/internal/scheduler/renew-gmail-watch",
                http_method=scheduler_v1.HttpMethod.POST,
                oidc_token=scheduler_v1.OidcToken(
                    service_account_email=service_account_email
                )
            ),
            retry_config=scheduler_v1.RetryConfig(
                retry_count=3,
                max_retry_duration=duration_pb2.Duration(seconds=3600),  # 1 hour max
                min_backoff_duration=duration_pb2.Duration(seconds=60),  # 1 min
                max_backoff_duration=duration_pb2.Duration(seconds=600),  # 10 min
                max_doublings=3
            )
        )
        
        updated_job = client.update_job(job=job)
        logger.info(f"Updated Cloud Scheduler job: {updated_job.name}")
        return updated_job
        
    except Exception:
        # Job doesn't exist, create it
        logger.info(f"Creating new Cloud Scheduler job '{job_name}'")
        
        job = scheduler_v1.Job(
            name=full_job_name,
            description="Automatically renew Gmail watch subscription every 6 days",
            schedule="0 0 */6 * *",  # Every 6 days at midnight UTC
            time_zone="UTC",
            http_target=scheduler_v1.HttpTarget(
                uri=f"{webhook_service_url}/internal/scheduler/renew-gmail-watch",
                http_method=scheduler_v1.HttpMethod.POST,
                oidc_token=scheduler_v1.OidcToken(
                    service_account_email=service_account_email
                )
            ),
            retry_config=scheduler_v1.RetryConfig(
                retry_count=3,
                max_retry_duration=duration_pb2.Duration(seconds=3600),  # 1 hour max
                min_backoff_duration=duration_pb2.Duration(seconds=60),  # 1 min
                max_backoff_duration=duration_pb2.Duration(seconds=600),  # 10 min
                max_doublings=3
            )
        )
        
        created_job = client.create_job(parent=parent, job=job)
        logger.info(f"Created Cloud Scheduler job: {created_job.name}")
        logger.info(f"Schedule: Every 6 days at midnight UTC")
        logger.info(f"Target: {webhook_service_url}/internal/scheduler/renew-gmail-watch")
        
        return created_job


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python scripts/setup_gmail_watch_scheduler.py <webhook_service_url> <service_account_email>")
        print()
        print("Example:")
        print("  python scripts/setup_gmail_watch_scheduler.py \\")
        print("    https://jetsmx-webhooks-xxx.run.app \\")
        print("    jetsmx-agent@jetsmx-agent.iam.gserviceaccount.com")
        print()
        print("To get your Cloud Run service URL:")
        print("  gcloud run services describe jetsmx-webhooks --region us-central1 --format='value(status.url)'")
        sys.exit(1)
    
    webhook_url = sys.argv[1]
    service_account = sys.argv[2]
    
    # Remove trailing slash from URL if present
    webhook_url = webhook_url.rstrip('/')
    
    logger.info(f"Setting up Gmail watch scheduler")
    logger.info(f"Webhook URL: {webhook_url}")
    logger.info(f"Service Account: {service_account}")
    
    try:
        job = create_gmail_watch_scheduler(webhook_url, service_account)
        print()
        print("✅ Gmail watch scheduler configured successfully!")
        print(f"Job Name: {job.name}")
        print(f"Schedule: {job.schedule} ({job.time_zone})")
        print(f"Next run: Check with 'gcloud scheduler jobs describe gmail-watch-renewal --location=us-central1'")
        print()
        print("To manually trigger the job:")
        print("  gcloud scheduler jobs run gmail-watch-renewal --location=us-central1")
        
    except Exception as e:
        logger.error(f"Failed to setup Gmail watch scheduler: {str(e)}")
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

