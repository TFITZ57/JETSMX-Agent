"""
Shared constants used across the application.
"""

# Airtable table names
TABLE_APPLICANTS = "applicants"
TABLE_APPLICANT_PIPELINE = "applicant_pipeline"
TABLE_INTERACTIONS = "interactions"
TABLE_CONTRACTORS = "contractors"
TABLE_AIRCRAFT_TYPES = "aircraft_types"
TABLE_ENGINE_FAMILIES = "engine_families"
TABLE_AIRPORTS = "airports"

# Pipeline stages
PIPELINE_STAGE_NEW = "New"
PIPELINE_STAGE_PROFILE_GENERATED = "Profile Generated"
PIPELINE_STAGE_HR_SCREEN_APPROVED = "HR Screen – Approved"
PIPELINE_STAGE_HR_SCREEN_DENIED = "HR Screen – Denied"
PIPELINE_STAGE_OUTREACH_DRAFT_CREATED = "Outreach Draft Created"
PIPELINE_STAGE_INITIAL_EMAIL_SENT = "Initial Email Sent"
PIPELINE_STAGE_AWAITING_APPLICANT_REPLY = "Awaiting Applicant Reply"
PIPELINE_STAGE_APPLICANT_RESPONDED = "Applicant Responded"
PIPELINE_STAGE_PHONE_PROBE_SCHEDULED = "Phone Probe Scheduled"
PIPELINE_STAGE_PHONE_PROBE_COMPLETE = "Phone Probe Complete"
PIPELINE_STAGE_VIDEO_INTERVIEW_SCHEDULED = "Video Interview Scheduled"
PIPELINE_STAGE_INTERVIEW_COMPLETE = "Interview Complete"
PIPELINE_STAGE_BACKGROUND_CHECK_PENDING = "Background Check – Pending"
PIPELINE_STAGE_BACKGROUND_CHECK_PASSED = "Background Check – Passed"
PIPELINE_STAGE_BACKGROUND_CHECK_FAILED = "Background Check – Failed"
PIPELINE_STAGE_READY_FOR_CONTRACTOR_ONBOARDING = "Ready for Contractor Onboarding"
PIPELINE_STAGE_ARCHIVED = "Archived / Not a Fit"

# Screening decisions
SCREENING_DECISION_APPROVE = "Approve"
SCREENING_DECISION_DENY = "Deny"
SCREENING_DECISION_NEEDS_REVIEW = "Needs Review"

# Interaction types
INTERACTION_TYPE_SYSTEM = "System"
INTERACTION_TYPE_EMAIL = "Email"
INTERACTION_TYPE_PHONE_CALL = "Phone Call"
INTERACTION_TYPE_VIDEO_INTERVIEW = "Video Interview"
INTERACTION_TYPE_CHAT_NOTE = "Chat Note"

# Interaction directions
INTERACTION_DIRECTION_INBOUND = "Inbound"
INTERACTION_DIRECTION_OUTBOUND = "Outbound"
INTERACTION_DIRECTION_SYSTEM = "System"

# Interaction channels
INTERACTION_CHANNEL_GMAIL = "Gmail"
INTERACTION_CHANNEL_CALENDAR = "Calendar"
INTERACTION_CHANNEL_DRIVE = "Drive"
INTERACTION_CHANNEL_CHAT = "Chat"
INTERACTION_CHANNEL_MANUAL = "Manual"

# Event triggers
TRIGGER_SCREENING_APPROVED = "SCREENING_APPROVED"
TRIGGER_INTERVIEW_COMPLETE = "INTERVIEW_COMPLETE"
TRIGGER_BACKGROUND_CHECK_PASSED = "BACKGROUND_CHECK_PASSED"
TRIGGER_APPLICANT_EMAIL_REPLY = "APPLICANT_EMAIL_REPLY"
TRIGGER_PROBE_TRANSCRIPT_UPLOADED = "PROBE_TRANSCRIPT_UPLOADED"
TRIGGER_INTERVIEW_TRANSCRIPT_UPLOADED = "INTERVIEW_TRANSCRIPT_UPLOADED"
TRIGGER_CHAT_SCHEDULE_PROBE = "CHAT_SCHEDULE_PROBE"
TRIGGER_CHAT_SCHEDULE_INTERVIEW = "CHAT_SCHEDULE_INTERVIEW"
TRIGGER_CHAT_QUERY_APPLICANT = "CHAT_QUERY_APPLICANT"

# Gmail scopes
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send"
]

# Calendar scopes
CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events"
]

# Drive scopes
DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file"
]

# Chat scopes
CHAT_SCOPES = [
    "https://www.googleapis.com/auth/chat.bot",
    "https://www.googleapis.com/auth/chat.messages"
]

# All scopes combined
ALL_SCOPES = GMAIL_SCOPES + CALENDAR_SCOPES + DRIVE_SCOPES + CHAT_SCOPES

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2
RETRY_MIN_WAIT = 1
RETRY_MAX_WAIT = 60

