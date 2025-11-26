#!/usr/bin/env python3
"""
Deploy Airtable Agent REST API to Cloud Run.
"""
import subprocess
import sys
from pathlib import Path
from shared.config.settings import get_settings

settings = get_settings()


def deploy_airtable_agent():
    """Deploy the Airtable Agent REST API service to Cloud Run."""
    project_root = Path(__file__).parent.parent
    
    print("🚀 Deploying Airtable Agent REST API to Cloud Run...")
    
    # Check if gcloud is configured
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            check=True
        )
        project_id = result.stdout.strip()
        print(f"✓ Using GCP project: {project_id}")
    except subprocess.CalledProcessError:
        print("❌ gcloud not configured. Run: gcloud auth login && gcloud config set project YOUR_PROJECT_ID")
        sys.exit(1)
    
    # Build and deploy using Cloud Build
    print("\n📦 Building and deploying with Cloud Build...")
    try:
        subprocess.run(
            [
                "gcloud", "builds", "submit",
                "--config", "infra/airtable_agent/cloudbuild.yaml",
                "."
            ],
            cwd=project_root,
            check=True
        )
        print("✓ Build and deployment successful!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)
    
    # Get service URL
    print("\n🔍 Retrieving service URL...")
    try:
        result = subprocess.run(
            [
                "gcloud", "run", "services", "describe",
                "jetsmx-airtable-agent",
                "--region", "us-central1",
                "--format", "value(status.url)"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        service_url = result.stdout.strip()
        print(f"\n✅ Airtable Agent deployed successfully!")
        print(f"\n📍 Service URL: {service_url}")
        print(f"\n🔑 API Endpoints:")
        print(f"   Health:       {service_url}/health")
        print(f"   Query:        {service_url}/airtable/query")
        print(f"   Schema:       {service_url}/airtable/schema")
        print(f"   Tables:       {service_url}/airtable/tables")
        print(f"\n📖 Full API docs: {service_url}/docs")
        
        # Test health endpoint
        print("\n🏥 Testing health endpoint...")
        import requests
        try:
            response = requests.get(f"{service_url}/health", timeout=10)
            if response.status_code == 200:
                print("✓ Health check passed!")
                health_data = response.json()
                print(f"  Status: {health_data.get('status')}")
                print(f"  Version: {health_data.get('version')}")
            else:
                print(f"⚠️ Health check returned status {response.status_code}")
        except Exception as e:
            print(f"⚠️ Could not test health endpoint: {e}")
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Could not retrieve service URL: {e}")
    
    print("\n💡 Next steps:")
    print("   1. Set AIRTABLE_AGENT_API_KEY secret if not already set")
    print("   2. Test the API with: curl {service_url}/health")
    print("   3. Try natural language query endpoint with POST to /airtable/query")


if __name__ == "__main__":
    deploy_airtable_agent()

