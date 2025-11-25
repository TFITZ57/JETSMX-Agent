"""
Gmail tools for Google ADK agents.
"""
from typing import Optional
from tools.gmail.drafts import create_draft_message, send_draft as _send_draft
from tools.gmail.messages import send_message as _send_message, get_message as _get_message
from tools.gmail.threads import get_thread as _get_thread, list_threads as _list_threads


def gmail_create_draft(to: str, subject: str, body: str, thread_id: Optional[str] = None) -> dict:
    """Create a Gmail draft.
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Email body (plain text)
        thread_id: Thread ID to reply to (optional)
        
    Returns:
        Draft info with draft_id, message_id, thread_id
    """
    return create_draft_message(to, subject, body, thread_id=thread_id)


def gmail_send_draft(
    draft_id: str,
    initiated_by: str,
    reason: str,
    applicant_id: Optional[str] = None
) -> dict:
    """Send a Gmail draft.
    
    Args:
        draft_id: Draft ID
        initiated_by: Who is initiating this send (agent name or user email)
        reason: Explicit reason for sending this draft
        applicant_id: Applicant ID for audit trail (optional)
        
    Returns:
        Message info with message_id, thread_id
    """
    return _send_draft(
        draft_id=draft_id,
        initiated_by=initiated_by,
        reason=reason,
        applicant_id=applicant_id
    )


def gmail_send_message(
    to: str,
    subject: str,
    body: str,
    initiated_by: str,
    reason: str,
    thread_id: Optional[str] = None,
    applicant_id: Optional[str] = None
) -> dict:
    """Send an email message directly.
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Email body (plain text)
        initiated_by: Who is initiating this email (agent name or user email)
        reason: Explicit reason for sending this email
        thread_id: Thread ID to reply to (optional)
        applicant_id: Applicant ID for audit trail (optional)
        
    Returns:
        Message info with message_id, thread_id
    """
    return _send_message(
        to=to,
        subject=subject,
        body=body,
        initiated_by=initiated_by,
        reason=reason,
        thread_id=thread_id,
        applicant_id=applicant_id
    )


def gmail_get_message(message_id: str) -> Optional[dict]:
    """Get a Gmail message by ID.
    
    Args:
        message_id: Message ID
        
    Returns:
        Message data or None
    """
    return _get_message(message_id)


def gmail_get_thread(thread_id: str) -> Optional[dict]:
    """Get a Gmail thread by ID.
    
    Args:
        thread_id: Thread ID
        
    Returns:
        Thread data with all messages or None
    """
    return _get_thread(thread_id)


def gmail_list_threads(query: Optional[str] = None, max_results: int = 10) -> list:
    """List Gmail threads matching a query.
    
    Args:
        query: Gmail search query (e.g., 'from:user@example.com')
        max_results: Maximum number of threads to return
        
    Returns:
        List of thread summaries
    """
    return _list_threads(query=query, max_results=max_results)


# Export all tools
ALL_GMAIL_TOOLS = [
    gmail_create_draft,
    gmail_send_draft,
    gmail_send_message,
    gmail_get_message,
    gmail_get_thread,
    gmail_list_threads
]

