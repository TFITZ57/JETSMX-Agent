"""
Audit trail helpers for tracking high-risk actions.
"""
from typing import Any, Dict, Optional
from datetime import datetime
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def log_audit_event(
    action: str,
    resource_type: str,
    resource_id: str,
    initiated_by: str,
    reason: str,
    agent_name: Optional[str] = None,
    user_id: Optional[str] = None,
    before_state: Optional[Dict[str, Any]] = None,
    after_state: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an audit trail event for actions that modify external resources.
    
    Args:
        action: Action performed (e.g., "email_sent", "airtable_updated", "event_created")
        resource_type: Type of resource (e.g., "gmail_message", "airtable_record", "calendar_event")
        resource_id: Unique identifier for the resource
        initiated_by: Who/what initiated this action (e.g., "hr_pipeline_agent", "tyler@jetstreammx.com", "applicant_analysis_agent")
        reason: Explicit reason for this action (e.g., "Sending initial probe call invitation to qualified applicant")
        agent_name: Name of the agent that performed the action (deprecated, use initiated_by)
        user_id: Human user who initiated the action (if applicable)
        before_state: State before the action (if applicable)
        after_state: State after the action (if applicable)
        metadata: Additional metadata about the action
    """
    audit_data = {
        "event_type": "audit",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "initiated_by": initiated_by,
        "reason": reason,
        "agent_name": agent_name or initiated_by,
        "user_id": user_id,
        "before_state": before_state,
        "after_state": after_state,
        "metadata": metadata or {}
    }
    
    logger.info(
        f"Audit: {action} on {resource_type} {resource_id} | Initiated by: {initiated_by} | Reason: {reason}",
        extra={"extra_fields": audit_data}
    )


def log_email_sent(
    to: str,
    subject: str,
    message_id: str,
    thread_id: Optional[str],
    initiated_by: str,
    reason: str,
    applicant_id: Optional[str] = None
) -> None:
    """
    Log an email sent event.
    
    Args:
        to: Recipient email address
        subject: Email subject line
        message_id: Gmail message ID
        thread_id: Gmail thread ID (if replying)
        initiated_by: Who initiated this email (agent name or user email)
        reason: Explicit reason for sending this email
        applicant_id: Airtable applicant record ID (if applicable)
    """
    log_audit_event(
        action="email_sent",
        resource_type="gmail_message",
        resource_id=message_id,
        initiated_by=initiated_by,
        reason=reason,
        metadata={
            "to": to,
            "subject": subject,
            "thread_id": thread_id,
            "applicant_id": applicant_id
        }
    )


def log_airtable_update(
    table: str,
    record_id: str,
    fields_updated: Dict[str, Any],
    initiated_by: str,
    reason: str,
    before_values: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an Airtable record update event.
    
    Args:
        table: Airtable table name
        record_id: Airtable record ID
        fields_updated: Dictionary of fields that were updated
        initiated_by: Who initiated this update (agent name or user email)
        reason: Explicit reason for this update
        before_values: Previous values of updated fields (if available)
    """
    log_audit_event(
        action="airtable_updated",
        resource_type="airtable_record",
        resource_id=f"{table}/{record_id}",
        initiated_by=initiated_by,
        reason=reason,
        before_state=before_values,
        after_state=fields_updated,
        metadata={"table": table}
    )


def log_calendar_event_created(
    event_id: str,
    summary: str,
    start_time: str,
    attendees: list,
    agent_name: str,
    applicant_id: Optional[str] = None
) -> None:
    """Log a calendar event creation."""
    log_audit_event(
        action="calendar_event_created",
        resource_type="calendar_event",
        resource_id=event_id,
        agent_name=agent_name,
        metadata={
            "summary": summary,
            "start_time": start_time,
            "attendees": attendees,
            "applicant_id": applicant_id
        }
    )


def log_workflow_execution(
    workflow_name: str,
    event_type: str,
    event_data: Dict[str, Any],
    status: str,
    result: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log workflow execution events.
    
    Args:
        workflow_name: Name of the workflow (e.g., "applicant_analysis")
        event_type: Type of event that triggered the workflow (e.g., "resume_upload")
        event_data: The event data that triggered the workflow
        status: Status of the workflow ("started", "completed", "failed", "error")
        result: Result of the workflow execution (if applicable)
    """
    log_audit_event(
        action=f"workflow_{status}",
        resource_type="workflow_execution",
        resource_id=f"{workflow_name}/{event_type}",
        initiated_by=f"{workflow_name}_workflow",
        reason=f"Processing {event_type} event",
        metadata={
            "workflow_name": workflow_name,
            "event_type": event_type,
            "status": status,
            "event_data": event_data,
            "result": result
        }
    )

