#!/usr/bin/env python3
"""
Deploy Applicant Analysis Agent to Vertex AI Agent Builder.

This script deploys the Google ADK-based Applicant Analysis Agent to Vertex AI,
making it available as a managed service with auto-scaling and monitoring.

Usage:
    python scripts/deploy_applicant_analysis_agent.py [--project PROJECT_ID] [--location LOCATION]
"""
import argparse
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from vertexai import init
from vertexai.preview import reasoning_engines
from agents.applicant_analysis.agent_adk import ApplicantAnalysisAgent
from shared.logging.logger import setup_logger
from shared.config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()


def deploy_agent(
    project_id: str = None,
    location: str = "us-central1",
    staging_bucket: str = None
):
    """
    Deploy the Applicant Analysis Agent to Vertex AI.
    
    Args:
        project_id: GCP project ID (defaults to settings)
        location: GCP region (defaults to us-central1)
        staging_bucket: GCS bucket for staging (defaults to settings)
        
    Returns:
        Deployed agent resource name
    """
    # Use defaults from settings if not provided
    project_id = project_id or settings.gcp_project_id
    staging_bucket = staging_bucket or settings.gcp_staging_bucket
    
    if not project_id:
        raise ValueError("GCP project ID must be provided or set in environment")
    
    logger.info(f"Deploying Applicant Analysis Agent to Vertex AI")
    logger.info(f"Project: {project_id}")
    logger.info(f"Location: {location}")
    logger.info(f"Staging bucket: {staging_bucket}")
    
    # Initialize Vertex AI
    init(project=project_id, location=location, staging_bucket=staging_bucket)
    
    # Create agent instance
    logger.info("Creating agent instance...")
    agent = ApplicantAnalysisAgent()
    agent_engine = agent._create_agent()
    
    # Define requirements
    requirements = [
        "google-cloud-aiplatform>=1.40.0",
        "langchain>=0.1.0",
        "langchain-core>=0.1.0",
        "langchain-google-vertexai>=0.1.0",
        "pyairtable>=2.1.0",
        "google-api-python-client>=2.100.0",
        "google-auth>=2.23.0",
        "google-cloud-pubsub>=2.18.0",
        "pdfplumber>=0.10.3",
        "PyPDF2>=3.0.1",
        "reportlab>=4.0.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0"
    ]
    
    # Deploy to Vertex AI
    logger.info("Deploying to Vertex AI (this may take several minutes)...")
    
    try:
        deployed_agent = reasoning_engines.ReasoningEngine.create(
            agent_engine,
            requirements=requirements,
            display_name="jetsmx-applicant-analysis-agent",
            description="Processes resumes and generates applicant profiles for JetsMX hiring workflow",
            sys_version="3.11"
        )
        
        logger.info(f"✓ Agent deployed successfully!")
        logger.info(f"Resource name: {deployed_agent.resource_name}")
        logger.info(f"Endpoint: {deployed_agent.gca_resource.name}")
        
        return deployed_agent.resource_name
        
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        raise


def list_deployed_agents(project_id: str = None, location: str = "us-central1"):
    """
    List all deployed reasoning engines in the project.
    
    Args:
        project_id: GCP project ID
        location: GCP region
    """
    project_id = project_id or settings.gcp_project_id
    
    if not project_id:
        raise ValueError("GCP project ID must be provided or set in environment")
    
    logger.info(f"Listing deployed agents in {project_id}/{location}")
    
    init(project=project_id, location=location)
    
    try:
        agents = reasoning_engines.ReasoningEngine.list()
        
        if not agents:
            logger.info("No agents deployed")
            return []
        
        logger.info(f"Found {len(agents)} deployed agent(s):")
        for agent in agents:
            logger.info(f"  - {agent.display_name} ({agent.resource_name})")
        
        return agents
        
    except Exception as e:
        logger.error(f"Failed to list agents: {str(e)}")
        raise


def delete_agent(resource_name: str, project_id: str = None, location: str = "us-central1"):
    """
    Delete a deployed reasoning engine.
    
    Args:
        resource_name: Full resource name of the agent
        project_id: GCP project ID
        location: GCP region
    """
    project_id = project_id or settings.gcp_project_id
    
    if not project_id:
        raise ValueError("GCP project ID must be provided or set in environment")
    
    logger.info(f"Deleting agent: {resource_name}")
    
    init(project=project_id, location=location)
    
    try:
        agent = reasoning_engines.ReasoningEngine(resource_name)
        agent.delete()
        
        logger.info(f"✓ Agent deleted successfully")
        
    except Exception as e:
        logger.error(f"Failed to delete agent: {str(e)}")
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Deploy Applicant Analysis Agent to Vertex AI"
    )
    
    parser.add_argument(
        "--project",
        type=str,
        help="GCP project ID (defaults to GCP_PROJECT_ID env var)"
    )
    
    parser.add_argument(
        "--location",
        type=str,
        default="us-central1",
        help="GCP region (default: us-central1)"
    )
    
    parser.add_argument(
        "--staging-bucket",
        type=str,
        help="GCS staging bucket (defaults to GCP_STAGING_BUCKET env var)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List deployed agents instead of deploying"
    )
    
    parser.add_argument(
        "--delete",
        type=str,
        metavar="RESOURCE_NAME",
        help="Delete the specified agent"
    )
    
    args = parser.parse_args()
    
    try:
        if args.list:
            list_deployed_agents(
                project_id=args.project,
                location=args.location
            )
        elif args.delete:
            delete_agent(
                resource_name=args.delete,
                project_id=args.project,
                location=args.location
            )
        else:
            resource_name = deploy_agent(
                project_id=args.project,
                location=args.location,
                staging_bucket=args.staging_bucket
            )
            
            print(f"\n{'='*60}")
            print(f"✓ Deployment successful!")
            print(f"{'='*60}")
            print(f"Resource: {resource_name}")
            print(f"\nTo use this agent:")
            print(f"  from agents.applicant_analysis.agent_adk import process_resume")
            print(f"  result = process_resume(file_id='...', filename='...')")
            print(f"{'='*60}\n")
            
    except Exception as e:
        logger.error(f"Operation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

