"""
Pydantic models for Applicant data.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class ApplicantCreate(BaseModel):
    """Model for creating a new applicant."""
    applicant_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    time_zone: Optional[str] = None
    resume_drive_file_id: Optional[str] = None
    resume_link: Optional[str] = None
    icc_pdf_drive_file_id: Optional[str] = None
    icc_pdf_link: Optional[str] = None
    has_faa_ap: bool = False
    faa_ap_number: Optional[str] = None
    other_certs: Optional[str] = None
    years_in_aviation: Optional[float] = None
    business_aviation_experience: bool = False
    aog_field_experience: bool = False
    geographic_flexibility: Optional[str] = None
    aog_suitability_score: Optional[float] = None
    baseline_verdict: Optional[str] = None
    missing_info_summary: Optional[str] = None
    follow_up_questions: Optional[str] = None
    source: Optional[str] = "Drive Resume"


class ApplicantUpdate(BaseModel):
    """Model for updating an applicant."""
    applicant_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    time_zone: Optional[str] = None
    resume_drive_file_id: Optional[str] = None
    resume_link: Optional[str] = None
    icc_pdf_drive_file_id: Optional[str] = None
    icc_pdf_link: Optional[str] = None
    has_faa_ap: Optional[bool] = None
    faa_ap_number: Optional[str] = None
    other_certs: Optional[str] = None
    years_in_aviation: Optional[float] = None
    business_aviation_experience: Optional[bool] = None
    aog_field_experience: Optional[bool] = None
    geographic_flexibility: Optional[str] = None
    aog_suitability_score: Optional[float] = None
    baseline_verdict: Optional[str] = None
    missing_info_summary: Optional[str] = None
    follow_up_questions: Optional[str] = None


class Applicant(BaseModel):
    """Full applicant model with all fields."""
    id: str
    applicant_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    time_zone: Optional[str] = None
    resume_drive_file_id: Optional[str] = None
    resume_link: Optional[str] = None
    icc_pdf_drive_file_id: Optional[str] = None
    icc_pdf_link: Optional[str] = None
    has_faa_ap: bool = False
    faa_ap_number: Optional[str] = None
    other_certs: Optional[str] = None
    years_in_aviation: Optional[float] = None
    business_aviation_experience: bool = False
    aog_field_experience: bool = False
    geographic_flexibility: Optional[str] = None
    aog_suitability_score: Optional[float] = None
    baseline_verdict: Optional[str] = None
    missing_info_summary: Optional[str] = None
    follow_up_questions: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[str] = None
    last_updated: Optional[str] = None

