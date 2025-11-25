"""
Pydantic models for Applicant Analysis Agent tool inputs and outputs.

These models provide type safety and validation for the Google ADK tools.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


# Tool Response Models

class ToolResponse(BaseModel):
    """Base model for all tool responses."""
    success: bool = Field(..., description="Whether the tool execution succeeded")
    error: Optional[str] = Field(None, description="Error message if tool failed")


class DownloadResumeResponse(ToolResponse):
    """Response from download_resume_from_drive tool."""
    pdf_content_base64: Optional[str] = Field(None, description="Base64-encoded PDF content")
    file_size_bytes: int = Field(0, description="Size of downloaded file in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type of file")


class ParsedResumeData(BaseModel):
    """Structured data extracted from resume."""
    raw_text: str = Field(..., description="Full text extracted from resume")
    applicant_name: Optional[str] = Field(None, description="Candidate name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="Location (City, ST)")
    has_faa_ap: bool = Field(False, description="Has FAA A&P license")
    faa_ap_number: Optional[str] = Field(None, description="A&P license number")
    years_in_aviation: Optional[float] = Field(None, description="Years of aviation experience")
    business_aviation_experience: bool = Field(False, description="Has business aviation experience")
    aog_field_experience: bool = Field(False, description="Has AOG/field service experience")
    text_length: int = Field(0, description="Length of extracted text")


class ParseResumeResponse(ToolResponse):
    """Response from parse_resume_text tool."""
    parsed_data: Optional[Dict[str, Any]] = Field(None, description="Extracted resume data")


class CandidateAnalysis(BaseModel):
    """LLM-generated analysis of candidate fit."""
    applicant_name: str = Field(..., description="Full name of applicant")
    aircraft_experience: str = Field(..., description="Aircraft families/types with experience")
    engine_experience: str = Field(..., description="Engine families with experience")
    systems_strengths: str = Field(..., description="Key system areas of strength")
    aog_suitability_score: int = Field(..., ge=0, le=10, description="AOG suitability score (1-10)")
    geographic_flexibility: str = Field(..., description="Geographic flexibility assessment")
    baseline_verdict: str = Field(..., description="Initial assessment verdict")
    missing_info: str = Field(..., description="List of missing critical information")
    follow_up_questions: str = Field(..., description="Questions to ask in probe call")


class AnalyzeCandidateResponse(ToolResponse):
    """Response from analyze_candidate_fit tool."""
    analysis: Optional[Dict[str, Any]] = Field(None, description="Candidate fit analysis")


class CreateRecordsResponse(ToolResponse):
    """Response from create_applicant_records_in_airtable tool."""
    applicant_id: Optional[str] = Field(None, description="Airtable Applicants record ID")
    pipeline_id: Optional[str] = Field(None, description="Airtable Pipeline record ID")


class GenerateICCResponse(ToolResponse):
    """Response from generate_icc_pdf tool."""
    pdf_content_base64: Optional[str] = Field(None, description="Base64-encoded ICC PDF")
    pdf_size_bytes: int = Field(0, description="Size of PDF in bytes")


class UploadICCResponse(ToolResponse):
    """Response from upload_icc_to_drive tool."""
    file_id: Optional[str] = Field(None, description="Drive file ID")
    web_view_link: Optional[str] = Field(None, description="Shareable Drive link")


class PublishEventResponse(ToolResponse):
    """Response from publish_completion_event tool."""
    message_id: Optional[str] = Field(None, description="Pub/Sub message ID")


# Agent Result Models

class ApplicantAnalysisResult(BaseModel):
    """Final result from the Applicant Analysis Agent workflow."""
    success: bool = Field(..., description="Whether processing completed successfully")
    applicant_id: Optional[str] = Field(None, description="Airtable Applicants record ID")
    pipeline_id: Optional[str] = Field(None, description="Airtable Pipeline record ID")
    icc_file_id: Optional[str] = Field(None, description="Drive file ID of ICC PDF")
    applicant_name: Optional[str] = Field(None, description="Extracted applicant name")
    baseline_verdict: Optional[str] = Field(
        None,
        description="Assessment verdict: Strong Fit, Maybe, Not a Fit, or Needs More Info"
    )
    error: Optional[str] = Field(None, description="Error message if processing failed")


# Tool Input Models (for documentation and validation)

class DownloadResumeInput(BaseModel):
    """Input parameters for download_resume_from_drive tool."""
    file_id: str = Field(..., description="Google Drive file ID")


class ParseResumeInput(BaseModel):
    """Input parameters for parse_resume_text tool."""
    pdf_content_base64: str = Field(..., description="Base64-encoded PDF content")


class AnalyzeCandidateInput(BaseModel):
    """Input parameters for analyze_candidate_fit tool."""
    parsed_resume_data: str = Field(..., description="JSON string of parsed resume data")


class CreateRecordsInput(BaseModel):
    """Input parameters for create_applicant_records_in_airtable tool."""
    parsed_data_json: str = Field(..., description="JSON string of parsed resume data")
    analysis_json: str = Field(..., description="JSON string of analysis results")
    resume_file_id: str = Field(..., description="Original resume Drive file ID")


class GenerateICCInput(BaseModel):
    """Input parameters for generate_icc_pdf tool."""
    parsed_data_json: str = Field(..., description="JSON string of parsed resume data")
    analysis_json: str = Field(..., description="JSON string of analysis results")


class UploadICCInput(BaseModel):
    """Input parameters for upload_icc_to_drive tool."""
    pdf_content_base64: str = Field(..., description="Base64-encoded PDF content")
    applicant_name: str = Field(..., description="Applicant name for filename")
    applicant_id: str = Field(..., description="Airtable record ID to update")
    parent_folder_id: Optional[str] = Field(None, description="Drive folder for storage")


class PublishEventInput(BaseModel):
    """Input parameters for publish_completion_event tool."""
    applicant_id: str = Field(..., description="Airtable applicant record ID")
    pipeline_id: str = Field(..., description="Pipeline record ID")
    baseline_verdict: str = Field(..., description="Assessment verdict")

