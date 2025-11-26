"""
Setup Cloud Scheduler to poll Drive folder every 2 minutes.
"""
import sys
from google.cloud import scheduler_v1
from google.cloud.scheduler_v1.types import HttpTarget, OidcToken
from google.protobuf import duration_pb2
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def create_drive_poller_scheduler(
    poller_url: str,
    service_account_email: str,
    schedule: str = "*/2 * * * *"  # Every 2 minutes
) -> scheduler_v1.Job:
    """
    Create Cloud Scheduler job to poll Drive folder.
    
    Args:
        poller_url: Cloud Run URL for drive poller
        service_account_email: Service account for OIDC auth
        schedule: Cron schedule (default: every 2 minutes)
    """
    settings = get_settings()
    client = scheduler_v1.CloudSchedulerClient()
    
    parent = f"projects/{settings.gcp_project_id}/locations/us-central1"
    job_name = f"{parent}/jobs/drive-folder-poller"
    
    # Check if job exists
    try:
        existing_job = client.get_job(name=job_name)
        logger.info(f"Cloud Scheduler job 'drive-folder-poller' already exists")
        
        # Update the existing job
        job = scheduler_v1.Job(
            name=job_name,
            description="Polls Drive resumes folder for new files",
            schedule=schedule,
            time_zone="America/New_York",
            http_target=HttpTarget(
                uri=poller_url,
                http_method=1,  # GET = 1
                oidc_token=OidcToken(
                    service_account_email=service_account_email,
                    audience=poller_url
                )
            ),
            retry_config=scheduler_v1.RetryConfig(
                retry_count=3,
                max_retry_duration=duration_pb2.Duration(seconds=600),
                min_backoff_duration=duration_pb2.Duration(seconds=5),
                max_backoff_duration=duration_pb2.Duration(seconds=60),
                max_doublings=3
            )
        )
        
        updated_job = client.update_job(job=job)
        logger.info(f"Updated Cloud Scheduler job: {updated_job.name}")
        return updated_job
        
    except Exception as e:
        if "not found" not in str(e).lower() and "404" not in str(e):
            logger.error(f"Error checking for existing job: {str(e)}")
            raise
        
        # Create new job
        logger.info("Creating new Cloud Scheduler job for Drive poller")
        
        job = scheduler_v1.Job(
            name=job_name,
            description="Polls Drive resumes folder for new files",
            schedule=schedule,
            time_zone="America/New_York",
            http_target=HttpTarget(
                uri=poller_url,
                http_method=1,  # GET = 1
                oidc_token=OidcToken(
                    service_account_email=service_account_email,
                    audience=poller_url
                )
            ),
            retry_config=scheduler_v1.RetryConfig(
                retry_count=3,
                max_retry_duration=duration_pb2.Duration(seconds=600),
                min_backoff_duration=duration_pb2.Duration(seconds=5),
                max_backoff_duration=duration_pb2.Duration(seconds=60),
                max_doublings=3
            )
        )
        
        created_job = client.create_job(parent=parent, job=job)
        logger.info(f"Created Cloud Scheduler job: {created_job.name}")
        return created_job


def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python setup_drive_poller_scheduler.py <POLLER_URL> <SERVICE_ACCOUNT_EMAIL>")
        print("Example: python setup_drive_poller_scheduler.py https://drive-poller-xxx.run.app jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com")
        sys.exit(1)
    
    poller_url = sys.argv[1]
    service_account_email = sys.argv[2]
    
    print("=" * 70)
    print("Setting up Drive Folder Poller Scheduler")
    print("=" * 70)
    print(f"Poller URL: {poller_url}")
    print(f"Service Account: {service_account_email}")
    print(f"Schedule: Every 2 minutes")
    print()
    
    try:
        job = create_drive_poller_scheduler(poller_url, service_account_email)
        print("✅ Drive folder poller scheduler configured")
        print(f"   Job: {job.name}")
        print(f"   Schedule: {job.schedule}")
        print()
        print("To manually trigger:")
        print("  gcloud scheduler jobs run drive-folder-poller --location=us-central1")
        
    except Exception as e:
        print(f"❌ Failed to setup scheduler: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

