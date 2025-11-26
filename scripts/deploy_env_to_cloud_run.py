#!/usr/bin/env python3
"""
Deploy environment variables from .env to Cloud Run services.

This script reads your local .env file and sets the environment variables
in your Cloud Run services automatically.
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import dotenv_values

def load_env_file():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    
    if not env_path.exists():
        print(f"❌ Error: .env file not found at {env_path}")
        print("Please copy env.template to .env and fill in your values.")
        return None
    
    # Load env vars
    env_vars = dotenv_values(env_path)
    
    # Filter out empty values and template placeholders
    filtered_vars = {
        k: v for k, v in env_vars.items() 
        if v and not v.startswith("YOUR_") and v != "N/A"
    }
    
    return filtered_vars

def build_env_var_string(env_vars):
    """Build the --set-env-vars string for gcloud."""
    # These are the critical ones for Cloud Run
    cloud_run_vars = [
        "OPENAI_API_KEY",
        "GCP_PROJECT_ID",
        "GCP_SERVICE_ACCOUNT_JSON_PATH",
        "AIRTABLE_API_KEY",
        "AIRTABLE_BASE_ID",
        "AIRTABLE_WEBHOOK_SECRET",
        "GMAIL_USER_EMAIL",
        "GMAIL_WATCH_TOPIC",
        "CALENDAR_ID",
        "GOOGLE_CHAT_SPACE_ID",
        "PUBSUB_TOPIC_AIRTABLE",
        "PUBSUB_TOPIC_GMAIL",
        "PUBSUB_TOPIC_DRIVE",
        "PUBSUB_TOPIC_CHAT",
        "DRIVE_FOLDER_RESUMES_INCOMING",
        "DRIVE_FOLDER_TRANSCRIPTS_PROBE",
        "DRIVE_FOLDER_TRANSCRIPTS_INTERVIEW",
        "ENVIRONMENT",
        "LOG_LEVEL",
        "WEBHOOK_SECRET",
        "WEBHOOK_BASE_URL",
        "VERTEX_AI_LOCATION",
    ]
    
    # Build the string
    env_string_parts = []
    for key in cloud_run_vars:
        if key in env_vars:
            value = env_vars[key]
            # Escape special characters
            value = value.replace('"', '\\"')
            env_string_parts.append(f"{key}={value}")
    
    return ",".join(env_string_parts)

def update_cloud_run_service(service_name, env_vars):
    """Update Cloud Run service with environment variables."""
    env_string = build_env_var_string(env_vars)
    
    if not env_string:
        print(f"⚠️  No environment variables to set for {service_name}")
        return False
    
    print(f"\n📦 Updating {service_name}...")
    print(f"   Setting {len(env_string.split(','))} environment variables")
    
    cmd = [
        "gcloud", "run", "services", "update", service_name,
        "--region", "us-central1",
        "--project", "jetsmx-agent",
        "--set-env-vars", env_string
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {service_name} updated successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to update {service_name}")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Main function."""
    print("=" * 70)
    print("Deploying Environment Variables to Cloud Run")
    print("=" * 70)
    
    # Load env vars
    env_vars = load_env_file()
    if not env_vars:
        return 1
    
    print(f"\n📋 Loaded {len(env_vars)} environment variables from .env")
    
    # Show what we're about to set (first few chars only for security)
    print("\n🔑 Environment variables to deploy:")
    for key, value in sorted(env_vars.items()):
        if len(value) > 20:
            display_value = value[:10] + "..." + value[-7:]
        else:
            display_value = value
        print(f"   {key}: {display_value}")
    
    # Confirm
    print("\n⚠️  This will update the following Cloud Run services:")
    print("   - jetsmx-pubsub-handler")
    print("   - jetsmx-webhooks")
    print("   - jetsmx-resume-uploader")
    
    # Check for --yes flag
    if "--yes" not in sys.argv and "-y" not in sys.argv:
        response = input("\n❓ Continue? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("❌ Aborted")
            return 1
    else:
        print("\n✅ Auto-confirmed with --yes flag")
    
    # Update services
    print("\n" + "=" * 70)
    
    success_count = 0
    
    # Update pubsub-handler
    if update_cloud_run_service("jetsmx-pubsub-handler", env_vars):
        success_count += 1
    
    # Update webhooks
    if update_cloud_run_service("jetsmx-webhooks", env_vars):
        success_count += 1
    
    # Update resume-uploader
    if update_cloud_run_service("jetsmx-resume-uploader", env_vars):
        success_count += 1
    
    # Summary
    print("\n" + "=" * 70)
    print(f"✅ Successfully updated {success_count}/3 services")
    print("=" * 70)
    
    if success_count == 3:
        print("\n🎉 All services updated with your environment variables!")
        print("\n📝 Next steps:")
        print("   1. Test resume processing:")
        print("      gcloud pubsub topics publish jetsmx-drive-events \\")
        print("        --project=jetsmx-agent \\")
        print("        --message='{\"event_type\":\"drive.file.created\",\"file_id\":\"YOUR_FILE_ID\",\"name\":\"resume.pdf\",\"mime_type\":\"application/pdf\",\"folder_type\":\"resumes\"}'")
        print("\n   2. Check logs:")
        print("      gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=jetsmx-pubsub-handler\" --limit=20 --project=jetsmx-agent")
        return 0
    else:
        print("\n⚠️  Some services failed to update. Check errors above.")
        return 1

if __name__ == "__main__":
    exit(main())

