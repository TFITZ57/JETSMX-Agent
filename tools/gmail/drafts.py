"""
Gmail draft management.
"""
import base64
from email.mime.text import MIMEText
from typing import Optional
from tools.gmail.client import get_gmail_client
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def create_draft_message(
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    thread_id: Optional[str] = None
) -> dict:
    """
    Create a Gmail draft.
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Email body (plain text or HTML)
        from_email: Sender email (defaults to authenticated user)
        thread_id: Thread ID to reply to
        
    Returns:
        Draft info with draft_id, message_id, thread_id
    """
    client = get_gmail_client()
    
    # Create message
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    if from_email:
        message['from'] = from_email
    
    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    # Build draft body
    draft_body = {
        'message': {
            'raw': raw_message
        }
    }
    
    if thread_id:
        draft_body['message']['threadId'] = thread_id
    
    try:
        draft = client.service.users().drafts().create(
            userId='me',
            body=draft_body
        ).execute()
        
        draft_id = draft['id']
        message_id = draft['message']['id']
        result_thread_id = draft['message'].get('threadId')
        
        logger.info(f"Created draft: {draft_id} for {to}")
        
        return {
            'draft_id': draft_id,
            'message_id': message_id,
            'thread_id': result_thread_id
        }
        
    except Exception as e:
        logger.error(f"Failed to create draft: {str(e)}")
        raise


def get_draft(draft_id: str) -> Optional[dict]:
    """
    Get a draft by ID.
    
    Args:
        draft_id: Draft ID
        
    Returns:
        Draft data or None
    """
    client = get_gmail_client()
    
    try:
        draft = client.service.users().drafts().get(
            userId='me',
            id=draft_id,
            format='full'
        ).execute()
        return draft
    except Exception as e:
        logger.error(f"Failed to get draft {draft_id}: {str(e)}")
        return None


def send_draft(
    draft_id: str,
    initiated_by: str,
    reason: str,
    applicant_id: Optional[str] = None
) -> dict:
    """
    Send a draft.
    
    Args:
        draft_id: Draft ID
        initiated_by: Who is initiating this send (agent name or user email)
        reason: Explicit reason for sending this draft
        applicant_id: Applicant ID for audit trail (optional)
        
    Returns:
        Sent message info
    """
    from shared.logging.audit import log_email_sent
    
    client = get_gmail_client()
    
    try:
        # Get draft details for audit log
        draft = get_draft(draft_id)
        if draft:
            headers = {}
            payload = draft.get('message', {}).get('payload', {})
            for header in payload.get('headers', []):
                headers[header['name']] = header['value']
            to = headers.get('To', 'unknown')
            subject = headers.get('Subject', 'unknown')
        else:
            to = 'unknown'
            subject = 'unknown'
        
        sent_message = client.service.users().drafts().send(
            userId='me',
            body={'id': draft_id}
        ).execute()
        
        message_id = sent_message['id']
        thread_id = sent_message.get('threadId')
        
        logger.info(f"Sent draft {draft_id} as message {message_id}")
        
        # Audit log
        log_email_sent(
            to=to,
            subject=subject,
            message_id=message_id,
            thread_id=thread_id,
            initiated_by=initiated_by,
            reason=reason,
            applicant_id=applicant_id
        )
        
        return {
            'message_id': message_id,
            'thread_id': thread_id
        }
        
    except Exception as e:
        logger.error(f"Failed to send draft {draft_id}: {str(e)}")
        raise


def delete_draft(draft_id: str) -> bool:
    """
    Delete a draft.
    
    Args:
        draft_id: Draft ID
        
    Returns:
        True if successful
    """
    client = get_gmail_client()
    
    try:
        client.service.users().drafts().delete(
            userId='me',
            id=draft_id
        ).execute()
        
        logger.info(f"Deleted draft {draft_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete draft {draft_id}: {str(e)}")
        return False

