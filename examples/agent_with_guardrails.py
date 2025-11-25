"""
Example: Using Gmail and Airtable Tools with Guardrails

This example demonstrates how to properly use the refactored Gmail and Airtable
tools that require explicit `reason` and `initiated_by` parameters for all
write operations.

All write operations now require:
- initiated_by: Who/what is performing this action (agent name or user email)
- reason: Explicit explanation for why this action is being taken
"""

from typing import Dict, Any
from tools.gmail.messages import send_message
from tools.gmail.drafts import send_draft
from tools.airtable.applicants import create_applicant, update_applicant
from tools.airtable.pipeline import create_pipeline_record, update_pipeline_record
from shared.models.applicant import ApplicantCreate, ApplicantUpdate
from shared.models.pipeline import PipelineCreate, PipelineUpdate


# ============================================================================
# Example 1: Sending an Email (with guardrails)
# ============================================================================

def example_send_email_to_applicant(
    applicant_email: str,
    applicant_name: str,
    applicant_id: str
) -> Dict[str, Any]:
    """
    Send an initial outreach email to a qualified applicant.
    
    This demonstrates the required guardrail parameters:
    - initiated_by: Identifies the agent or user
    - reason: Explains why the email is being sent
    """
    
    # Create email content
    subject = f"JetsMX - Exciting Opportunity for {applicant_name}"
    body = f"""
    Hi {applicant_name},
    
    We reviewed your application and are impressed with your A&P certification
    and aircraft maintenance experience. We'd like to schedule a brief phone
    call to discuss potential opportunities with JetsMX.
    
    Please reply with your availability over the next few days.
    
    Best regards,
    JetsMX Hiring Team
    """
    
    # Send with explicit guardrails
    result = send_message(
        to=applicant_email,
        subject=subject,
        body=body,
        initiated_by="hr_pipeline_agent",  # Required: who is sending
        reason=f"Sending initial probe call invitation to qualified applicant {applicant_id} who passed resume screening",  # Required: why
        applicant_id=applicant_id  # Optional: for tracking
    )
    
    return result


# ============================================================================
# Example 2: Sending a Draft (with guardrails)
# ============================================================================

def example_send_draft_after_approval(
    draft_id: str,
    applicant_id: str,
    approved_by: str
) -> Dict[str, Any]:
    """
    Send a draft email after human approval.
    
    Note: The draft was created earlier, but sending requires guardrails.
    """
    
    result = send_draft(
        draft_id=draft_id,
        initiated_by=f"hr_pipeline_agent_on_behalf_of_{approved_by}",  # Required
        reason=f"Human-approved outreach to applicant {applicant_id} following probe call",  # Required
        applicant_id=applicant_id  # Optional
    )
    
    return result


# ============================================================================
# Example 3: Creating an Applicant Record (with guardrails)
# ============================================================================

def example_create_applicant_from_resume(
    resume_data: Dict[str, Any]
) -> str:
    """
    Create an applicant record after parsing a resume.
    
    This shows how to use guardrails when creating records.
    """
    
    # Prepare applicant data
    applicant_data = ApplicantCreate(
        full_name=resume_data.get("name"),
        email=resume_data.get("email"),
        phone=resume_data.get("phone"),
        ap_license_number=resume_data.get("ap_number"),
        has_ap_license=bool(resume_data.get("ap_number")),
        years_experience=resume_data.get("years_exp"),
        aircraft_types_experience=resume_data.get("aircraft_types", [])
    )
    
    # Create record with guardrails
    record_id = create_applicant(
        data=applicant_data,
        initiated_by="applicant_analysis_agent",  # Required: which agent
        reason=f"New applicant profile created from resume analysis for {resume_data.get('name')}"  # Required: why
    )
    
    return record_id


# ============================================================================
# Example 4: Updating an Applicant Record (with guardrails)
# ============================================================================

def example_update_applicant_after_probe_call(
    applicant_record_id: str,
    probe_call_insights: Dict[str, Any]
) -> bool:
    """
    Update an applicant record with information gathered during probe call.
    """
    
    # Prepare update data
    update_data = ApplicantUpdate(
        on_call_availability=probe_call_insights.get("on_call_willing"),
        salary_expectations=probe_call_insights.get("expected_rate"),
        notes=probe_call_insights.get("summary")
    )
    
    # Update with guardrails
    success = update_applicant(
        record_id=applicant_record_id,
        data=update_data,
        initiated_by="hr_pipeline_agent",  # Required
        reason=f"Updating applicant {applicant_record_id} with probe call insights"  # Required
    )
    
    return success


# ============================================================================
# Example 5: Creating a Pipeline Record (with guardrails)
# ============================================================================

def example_create_pipeline_for_new_applicant(
    applicant_record_id: str
) -> str:
    """
    Create a pipeline record for a newly profiled applicant.
    """
    
    pipeline_data = PipelineCreate(
        applicant=applicant_record_id,
        pipeline_stage="PROFILE_GENERATED"
    )
    
    pipeline_id = create_pipeline_record(
        data=pipeline_data,
        initiated_by="applicant_analysis_agent",  # Required
        reason=f"Initializing pipeline tracking for applicant {applicant_record_id}"  # Required
    )
    
    return pipeline_id


# ============================================================================
# Example 6: Updating a Pipeline Record (with guardrails)
# ============================================================================

def example_update_pipeline_after_email_sent(
    pipeline_record_id: str,
    gmail_thread_id: str,
    gmail_message_id: str
) -> bool:
    """
    Update pipeline after initial outreach email is sent.
    """
    
    update_data = PipelineUpdate(
        pipeline_stage="INITIAL_EMAIL_SENT",
        outreach_thread_id=gmail_thread_id,
        last_outreach_message_id=gmail_message_id
    )
    
    success = update_pipeline_record(
        record_id=pipeline_record_id,
        data=update_data,
        initiated_by="hr_pipeline_agent",  # Required
        reason=f"Pipeline {pipeline_record_id} advanced to INITIAL_EMAIL_SENT stage"  # Required
    )
    
    return success


# ============================================================================
# Example 7: Complete Workflow with Guardrails
# ============================================================================

def example_complete_workflow(
    resume_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Complete workflow from resume to initial email with all guardrails.
    
    This demonstrates a real-world scenario where multiple write operations
    are performed, each with proper guardrails.
    """
    
    # Step 1: Create applicant record
    print("Step 1: Creating applicant record...")
    applicant_id = create_applicant(
        data=ApplicantCreate(
            full_name=resume_data["name"],
            email=resume_data["email"],
            phone=resume_data["phone"],
            has_ap_license=True
        ),
        initiated_by="applicant_analysis_agent",
        reason=f"New qualified applicant {resume_data['name']} from resume screening"
    )
    print(f"✓ Created applicant: {applicant_id}")
    
    # Step 2: Create pipeline record
    print("Step 2: Creating pipeline record...")
    pipeline_id = create_pipeline_record(
        data=PipelineCreate(
            applicant=applicant_id,
            pipeline_stage="PROFILE_GENERATED"
        ),
        initiated_by="applicant_analysis_agent",
        reason=f"Initializing hiring pipeline for applicant {applicant_id}"
    )
    print(f"✓ Created pipeline: {pipeline_id}")
    
    # Step 3: Send initial email
    print("Step 3: Sending initial outreach email...")
    email_result = send_message(
        to=resume_data["email"],
        subject=f"JetsMX - Opportunity for {resume_data['name']}",
        body="We'd like to discuss opportunities with you...",
        initiated_by="hr_pipeline_agent",
        reason=f"Initial outreach to qualified applicant {applicant_id}",
        applicant_id=applicant_id
    )
    print(f"✓ Sent email: {email_result['message_id']}")
    
    # Step 4: Update pipeline with email info
    print("Step 4: Updating pipeline with email tracking...")
    update_success = update_pipeline_record(
        record_id=pipeline_id,
        data=PipelineUpdate(
            pipeline_stage="INITIAL_EMAIL_SENT",
            outreach_thread_id=email_result['thread_id'],
            last_outreach_message_id=email_result['message_id']
        ),
        initiated_by="hr_pipeline_agent",
        reason=f"Marking pipeline {pipeline_id} as email sent with tracking IDs"
    )
    print(f"✓ Updated pipeline: {update_success}")
    
    return {
        "applicant_id": applicant_id,
        "pipeline_id": pipeline_id,
        "email_message_id": email_result['message_id'],
        "email_thread_id": email_result['thread_id']
    }


# ============================================================================
# Expected Audit Log Output
# ============================================================================

"""
When the above functions are called, you'll see structured JSON audit logs
like these in stdout:

{
  "timestamp": "2025-11-24T15:30:00.123456Z",
  "level": "INFO",
  "logger": "shared.logging.audit",
  "message": "Audit: email_sent on gmail_message msg_abc123 | Initiated by: hr_pipeline_agent | Reason: Sending initial probe call invitation to qualified applicant rec_xyz789 who passed resume screening",
  "event_type": "audit",
  "action": "email_sent",
  "resource_type": "gmail_message",
  "resource_id": "msg_abc123",
  "initiated_by": "hr_pipeline_agent",
  "reason": "Sending initial probe call invitation to qualified applicant rec_xyz789 who passed resume screening",
  "agent_name": "hr_pipeline_agent",
  "user_id": null,
  "before_state": null,
  "after_state": null,
  "metadata": {
    "to": "john.doe@example.com",
    "subject": "JetsMX - Exciting Opportunity for John Doe",
    "thread_id": "thread_def456",
    "applicant_id": "rec_xyz789"
  }
}

{
  "timestamp": "2025-11-24T15:30:01.234567Z",
  "level": "INFO",
  "logger": "shared.logging.audit",
  "message": "Audit: airtable_updated on airtable_record Applicants/rec_xyz789 | Initiated by: applicant_analysis_agent | Reason: New qualified applicant John Doe from resume screening",
  "event_type": "audit",
  "action": "airtable_updated",
  "resource_type": "airtable_record",
  "resource_id": "Applicants/rec_xyz789",
  "initiated_by": "applicant_analysis_agent",
  "reason": "New qualified applicant John Doe from resume screening",
  "agent_name": "applicant_analysis_agent",
  "user_id": null,
  "before_state": null,
  "after_state": {
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-0123",
    "has_ap_license": true
  },
  "metadata": {
    "table": "Applicants"
  }
}

These logs provide:
- Complete audit trail of who did what and why
- Timestamps for compliance and debugging
- Before/after states for reversibility
- Resource IDs for traceability
"""


# ============================================================================
# Anti-Patterns (DO NOT DO THIS)
# ============================================================================

"""
# ❌ WRONG - Missing required parameters
def bad_example_no_guardrails():
    # This will fail - missing initiated_by and reason
    send_message(
        to="applicant@example.com",
        subject="Job Opportunity",
        body="We want to hire you"
    )

# ❌ WRONG - Vague or meaningless reason
def bad_example_vague_reason():
    send_message(
        to="applicant@example.com",
        subject="Job Opportunity",
        body="We want to hire you",
        initiated_by="hr_pipeline_agent",
        reason="sending email"  # Too vague!
    )

# ✅ CORRECT - Specific, actionable reason
def good_example_specific_reason():
    send_message(
        to="applicant@example.com",
        subject="Job Opportunity",
        body="We want to hire you",
        initiated_by="hr_pipeline_agent",
        reason="Sending offer letter to applicant rec_123 after successful interview on 2025-11-20"
    )
"""


if __name__ == "__main__":
    # Example usage
    print("=" * 80)
    print("Example: Agent with Guardrails")
    print("=" * 80)
    print()
    
    # Mock resume data
    mock_resume = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0123",
        "ap_number": "123456789",
        "years_exp": 10,
        "aircraft_types": ["Cessna Citation", "Gulfstream G650"]
    }
    
    print("Running complete workflow with guardrails...")
    print()
    
    # Note: This would actually run if credentials are configured
    # result = example_complete_workflow(mock_resume)
    # print()
    # print("Workflow complete!")
    # print(f"Results: {result}")
    
    print("See function definitions above for usage examples.")
    print("All write operations now require 'initiated_by' and 'reason' parameters.")

