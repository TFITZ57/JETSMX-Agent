"""
Pydantic models for Applicant Pipeline data.
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PipelineCreate(BaseModel):
    """Model for creating a new pipeline record."""
    applicant: str  # Airtable record ID
    pipeline_stage: str = "New"
    screening_decision: Optional[str] = None
    screening_notes: Optional[str] = None


class PipelineUpdate(BaseModel):
    """Model for updating a pipeline record."""
    pipeline_stage: Optional[str] = None
    screening_decision: Optional[str] = None
    screening_notes: Optional[str] = None
    outreach_email_draft_id: Optional[str] = None
    outreach_thread_id: Optional[str] = None
    initial_email_sent_at: Optional[datetime] = None
    last_reply_received_at: Optional[datetime] = None
    last_reply_summary: Optional[str] = None
    preferred_call_window_1: Optional[str] = None
    preferred_call_window_2: Optional[str] = None
    confirmed_phone_number: Optional[str] = None
    constraints: Optional[str] = None
    probe_call_event_id: Optional[str] = None
    probe_call_datetime: Optional[datetime] = None
    probe_call_meet_link: Optional[str] = None
    probe_call_transcript_file_id: Optional[str] = None
    probe_call_transcript_link: Optional[str] = None
    interview_event_id: Optional[str] = None
    interview_datetime: Optional[datetime] = None
    interview_meet_link: Optional[str] = None
    interview_transcript_file_id: Optional[str] = None
    interview_transcript_link: Optional[str] = None
    run_background_check: Optional[bool] = None
    background_check_status: Optional[str] = None
    background_check_notes: Optional[str] = None
    email_draft_generated: Optional[bool] = None
    initial_chat_notified: Optional[bool] = None
    probe_chat_notified: Optional[bool] = None
    interview_chat_notified: Optional[bool] = None
    contractor_created: Optional[bool] = None


class Pipeline(BaseModel):
    """Full pipeline model."""
    id: str
    applicant: str
    applicant_name: Optional[str] = None
    primary_email: Optional[str] = None
    pipeline_stage: str
    stage_last_updated: Optional[datetime] = None
    screening_decision: Optional[str] = None
    screening_notes: Optional[str] = None
    outreach_email_draft_id: Optional[str] = None
    outreach_thread_id: Optional[str] = None
    initial_email_sent_at: Optional[datetime] = None
    last_reply_received_at: Optional[datetime] = None
    last_reply_summary: Optional[str] = None
    preferred_call_window_1: Optional[str] = None
    preferred_call_window_2: Optional[str] = None
    confirmed_phone_number: Optional[str] = None
    constraints: Optional[str] = None
    probe_call_event_id: Optional[str] = None
    probe_call_datetime: Optional[datetime] = None
    probe_call_meet_link: Optional[str] = None
    probe_call_transcript_file_id: Optional[str] = None
    probe_call_transcript_link: Optional[str] = None
    interview_event_id: Optional[str] = None
    interview_datetime: Optional[datetime] = None
    interview_meet_link: Optional[str] = None
    interview_transcript_file_id: Optional[str] = None
    interview_transcript_link: Optional[str] = None
    run_background_check: Optional[bool] = None
    background_check_status: Optional[str] = None
    background_check_notes: Optional[str] = None
    email_draft_generated: Optional[bool] = None
    initial_chat_notified: Optional[bool] = None
    probe_chat_notified: Optional[bool] = None
    interview_chat_notified: Optional[bool] = None
    contractor_created: Optional[bool] = None

