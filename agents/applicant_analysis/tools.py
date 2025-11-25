"""
Google ADK Tools for Applicant Analysis Agent.

Pure Python functions for use with Vertex AI Agent.
Tools follow a consistent pattern: return Dict[str, Any] with success, data, and error fields.
"""
import base64
import json
from typing import Dict, Any, Optional
from datetime import datetime
import vertexai
from vertexai.generative_models import GenerativeModel

from tools.drive.files import download_file, upload_file
from tools.airtable.applicants import create_applicant, update_applicant
from tools.airtable.pipeline import create_pipeline_record
from tools.airtable.interactions import log_interaction
from tools.pubsub.publisher import publish_event
from agents.applicant_analysis.resume_parser import parse_resume
from agents.applicant_analysis.icc_generator import generate_icc_pdf as generate_icc_pdf_bytes
from agents.applicant_analysis.prompts import SYSTEM_PROMPT, build_analysis_prompt
from shared.models.applicant import ApplicantCreate, ApplicantUpdate
from shared.models.pipeline import PipelineCreate
from shared.logging.logger import setup_logger
from shared.config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()

# Initialize Vertex AI
vertexai.init(project=settings.gcp_project_id, location=settings.vertex_ai_location)


def download_resume_from_drive(file_id: str) -> Dict[str, Any]:
    """
    Download a resume PDF from Google Drive.
    
    Args:
        file_id: The Google Drive file ID
        
    Returns:
        Dictionary with success status, base64-encoded PDF content, and metadata
    """
    try:
        logger.info(f"Downloading resume from Drive: {file_id}")
        content = download_file(file_id)
        
        if not content:
            return {
                "success": False,
                "error": "Failed to download file - no content returned",
                "pdf_content_base64": None,
                "file_size_bytes": 0
            }
        
        result = {
            "success": True,
            "pdf_content_base64": base64.b64encode(content).decode('utf-8'),
            "file_size_bytes": len(content),
            "mime_type": "application/pdf",
            "error": None
        }
        
        logger.info(f"Successfully downloaded {len(content)} bytes")
        return result
        
    except Exception as e:
        logger.error(f"Failed to download resume: {str(e)}")
        return {
            "success": False,
            "error": f"Download failed: {str(e)}",
            "pdf_content_base64": None,
            "file_size_bytes": 0
        }


def parse_resume_text(pdf_content_base64: str) -> Dict[str, Any]:
    """
    Parse resume PDF and extract structured data including contact info, licensing, and experience.
    
    Args:
        pdf_content_base64: Base64-encoded PDF content
        
    Returns:
        Dictionary with parsed data including contact info, licensing, and experience
    """
    try:
        logger.info("Parsing resume text")
        
        # Decode base64 to bytes
        pdf_bytes = base64.b64decode(pdf_content_base64)
        
        # Use existing parser
        parsed_data = parse_resume(pdf_bytes)
        
        if not parsed_data:
            return {
                "success": False,
                "error": "Failed to parse resume - no data extracted",
                "parsed_data": {}
            }
        
        result = {
            "success": True,
            "parsed_data": parsed_data,
            "error": None
        }
        
        logger.info(f"Successfully parsed resume: {parsed_data.get('email', 'unknown')}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to parse resume: {str(e)}")
        return {
            "success": False,
            "error": f"Parse failed: {str(e)}",
            "parsed_data": {}
        }


def analyze_candidate_fit(parsed_resume_data: str) -> Dict[str, Any]:
    """
    Analyze candidate suitability for AOG technician positions using LLM.
    
    Args:
        parsed_resume_data: JSON string of parsed resume data (use json.dumps() to convert dict)
        
    Returns:
        Dictionary with analysis including fit assessment, experience summary, and recommendations
    """
    try:
        logger.info("Analyzing candidate fit with LLM")
        
        # Parse input if it's a JSON string
        if isinstance(parsed_resume_data, str):
            parsed_data = json.loads(parsed_resume_data)
        else:
            parsed_data = parsed_resume_data
        
        # Initialize Gemini model
        model = GenerativeModel("gemini-1.5-pro")
        
        # Build prompt combining system and user instructions
        prompt = build_analysis_prompt(parsed_data)
        full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
        
        # Get LLM response
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 2048,
            }
        )
        response_text = response.text
        
        # Parse JSON from response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        else:
            json_text = response_text
        
        analysis = json.loads(json_text)
        
        result = {
            "success": True,
            "analysis": analysis,
            "error": None
        }
        
        logger.info(f"LLM analysis complete: {analysis.get('baseline_verdict', 'N/A')}")
        return result
        
    except Exception as e:
        logger.error(f"LLM analysis failed: {str(e)}")
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}",
            "analysis": {
                "applicant_name": "Unknown",
                "baseline_verdict": "Needs Review",
                "missing_info": f"Automated analysis failed: {str(e)}",
                "aog_suitability_score": 0
            }
        }


def create_applicant_records_in_airtable(
    parsed_data_json: str,
    analysis_json: str,
    resume_file_id: str
) -> Dict[str, Any]:
    """
    Create Applicants and Applicant Pipeline records in Airtable.
    
    Args:
        parsed_data_json: JSON string of parsed resume data
        analysis_json: JSON string of LLM analysis results
        resume_file_id: Original resume Drive file ID
        
    Returns:
        Dictionary with applicant_id and pipeline_id
    """
    try:
        logger.info("Creating Airtable records")
        
        # Parse JSON inputs
        parsed_data = json.loads(parsed_data_json) if isinstance(parsed_data_json, str) else parsed_data_json
        analysis = json.loads(analysis_json) if isinstance(analysis_json, str) else analysis_json
        
        # Build applicant data
        applicant_data = ApplicantCreate(
            applicant_name=analysis.get('applicant_name', 'Unknown'),
            email=parsed_data.get('email'),
            phone=parsed_data.get('phone'),
            location=parsed_data.get('location'),
            has_faa_ap=parsed_data.get('has_faa_ap', False),
            faa_ap_number=parsed_data.get('faa_ap_number'),
            years_in_aviation=parsed_data.get('years_in_aviation'),
            business_aviation_experience=parsed_data.get('business_aviation_experience', False),
            aog_field_experience=parsed_data.get('aog_field_experience', False),
            resume_drive_file_id=resume_file_id,
            geographic_flexibility=analysis.get('geographic_flexibility'),
            aog_suitability_score=analysis.get('aog_suitability_score'),
            baseline_verdict=analysis.get('baseline_verdict'),
            missing_info_summary=analysis.get('missing_info'),
            follow_up_questions=analysis.get('follow_up_questions'),
            source="Drive Resume"
        )
        
        # Create applicant
        applicant_id = create_applicant(applicant_data)
        
        # Create pipeline record
        pipeline_data = PipelineCreate(
            applicant=applicant_id,
            pipeline_stage="Profile Generated"
        )
        
        pipeline_id = create_pipeline_record(pipeline_data)
        
        # Log interaction
        log_interaction(
            applicant_id=applicant_id,
            interaction_type="System",
            direction="System",
            channel="Drive",
            summary=f"Resume processed and profile generated by Applicant Analysis Agent"
        )
        
        result = {
            "success": True,
            "applicant_id": applicant_id,
            "pipeline_id": pipeline_id,
            "error": None
        }
        
        logger.info(f"Created applicant {applicant_id} and pipeline {pipeline_id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to create Airtable records: {str(e)}")
        return {
            "success": False,
            "error": f"Airtable creation failed: {str(e)}",
            "applicant_id": None,
            "pipeline_id": None
        }


def generate_icc_pdf(parsed_data_json: str, analysis_json: str) -> Dict[str, Any]:
    """
    Generate Initial Candidate Coverage (ICC) PDF report.
    
    Args:
        parsed_data_json: JSON string of parsed resume data
        analysis_json: JSON string of analysis results
        
    Returns:
        Dictionary with base64-encoded PDF content
    """
    try:
        logger.info("Generating ICC PDF")
        
        # Parse JSON inputs
        parsed_data = json.loads(parsed_data_json) if isinstance(parsed_data_json, str) else parsed_data_json
        analysis = json.loads(analysis_json) if isinstance(analysis_json, str) else analysis_json
        
        # Ensure applicant_name is in parsed_data for ICC generation
        if 'applicant_name' not in parsed_data and 'applicant_name' in analysis:
            parsed_data['applicant_name'] = analysis['applicant_name']
        
        # Generate ICC PDF bytes
        icc_pdf_bytes = generate_icc_pdf_bytes(
            applicant_data=parsed_data,
            analysis=analysis
        )
        
        if not icc_pdf_bytes:
            return {
                "success": False,
                "error": "Failed to generate ICC PDF - no content",
                "pdf_content_base64": None,
                "pdf_size_bytes": 0
            }
        
        result = {
            "success": True,
            "pdf_content_base64": base64.b64encode(icc_pdf_bytes).decode('utf-8'),
            "pdf_size_bytes": len(icc_pdf_bytes),
            "error": None
        }
        
        logger.info(f"Generated ICC PDF: {len(icc_pdf_bytes)} bytes")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate ICC PDF: {str(e)}")
        return {
            "success": False,
            "error": f"ICC generation failed: {str(e)}",
            "pdf_content_base64": None,
            "pdf_size_bytes": 0
        }


def upload_icc_to_drive(
    pdf_content_base64: str,
    applicant_name: str,
    applicant_id: str,
    parent_folder_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Upload ICC PDF to Drive and update Applicant record with file reference.
    
    Args:
        pdf_content_base64: Base64-encoded PDF content
        applicant_name: Applicant name for filename
        applicant_id: Airtable record ID to update
        parent_folder_id: Optional Drive folder ID for storage
        
    Returns:
        Dictionary with file_id and web_view_link
    """
    try:
        logger.info(f"Uploading ICC to Drive for {applicant_name}")
        
        # Decode PDF
        pdf_bytes = base64.b64decode(pdf_content_base64)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f"ICC_{applicant_name.replace(' ', '_')}_{timestamp}.pdf"
        
        # Upload to Drive
        file_id = upload_file(
            name=filename,
            content=pdf_bytes,
            mime_type='application/pdf',
            parent_folder_id=parent_folder_id
        )
        
        if not file_id:
            return {
                "success": False,
                "error": "Failed to upload file to Drive",
                "file_id": None,
                "web_view_link": None
            }
        
        # Generate web view link
        web_view_link = f"https://drive.google.com/file/d/{file_id}/view"
        
        # Update Applicant record with ICC file reference
        update_applicant(
            applicant_id,
            ApplicantUpdate(
                icc_pdf_drive_file_id=file_id,
                icc_pdf_link=web_view_link
            )
        )
        
        result = {
            "success": True,
            "file_id": file_id,
            "web_view_link": web_view_link,
            "error": None
        }
        
        logger.info(f"Uploaded ICC: {file_id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to upload ICC: {str(e)}")
        return {
            "success": False,
            "error": f"Upload failed: {str(e)}",
            "file_id": None,
            "web_view_link": None
        }


def publish_completion_event(
    applicant_id: str,
    pipeline_id: str,
    baseline_verdict: str
) -> Dict[str, Any]:
    """
    Publish applicant_profile_created event to Pub/Sub for downstream workflows.
    
    Args:
        applicant_id: Airtable applicant record ID
        pipeline_id: Pipeline record ID
        baseline_verdict: Assessment verdict
        
    Returns:
        Dictionary with message_id
    """
    try:
        logger.info(f"Publishing completion event for applicant {applicant_id}")
        
        event_data = {
            "event_type": "applicant_profile_created",
            "applicant_id": applicant_id,
            "pipeline_id": pipeline_id,
            "baseline_verdict": baseline_verdict,
            "timestamp": datetime.now().isoformat(),
            "source": "applicant_analysis_agent"
        }
        
        # Publish to applicant events topic
        message_id = publish_event(
            topic_name="jetsmx-applicant-events",
            event_data=event_data
        )
        
        result = {
            "success": True,
            "message_id": message_id,
            "error": None
        }
        
        logger.info(f"Published event: {message_id}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to publish event: {str(e)}")
        return {
            "success": False,
            "error": f"Event publication failed: {str(e)}",
            "message_id": None
        }

