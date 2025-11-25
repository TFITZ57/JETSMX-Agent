"""
Gmail message operations.
"""
import base64
from typing import Optional, List, Dict, Any
from email.mime.text import MIMEText
from tools.gmail.client import get_gmail_client
from shared.logging.logger import setup_logger
from shared.logging.audit import log_email_sent

logger = setup_logger(__name__)


def get_message(message_id: str, format: str = 'full') -> Optional[dict]:
    """
    Get a message by ID.
    
    Args:
        message_id: Message ID
        format: Response format (minimal, full, raw, metadata)
        
    Returns:
        Message data or None
    """
    client = get_gmail_client()
    
    try:
        message = client.service.users().messages().get(
            userId='me',
            id=message_id,
            format=format
        ).execute()
        return message
    except Exception as e:
        logger.error(f"Failed to get message {message_id}: {str(e)}")
        return None


def send_message(
    to: str,
    subject: str,
    body: str,
    initiated_by: str,
    reason: str,
    from_email: Optional[str] = None,
    thread_id: Optional[str] = None,
    applicant_id: Optional[str] = None
) -> dict:
    """
    Send an email message.
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Email body (plain text or HTML)
        initiated_by: Who is initiating this email (agent name or user email)
        reason: Explicit reason for sending this email
        from_email: Sender email
        thread_id: Thread ID to reply to
        applicant_id: Applicant ID for audit trail
        
    Returns:
        Message info with message_id and thread_id
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
    
    # Build message body
    message_body = {
        'raw': raw_message
    }
    
    if thread_id:
        message_body['threadId'] = thread_id
    
    try:
        sent_message = client.service.users().messages().send(
            userId='me',
            body=message_body
        ).execute()
        
        message_id = sent_message['id']
        result_thread_id = sent_message.get('threadId')
        
        logger.info(f"Sent message: {message_id} to {to}")
        
        # Audit log
        log_email_sent(
            to=to,
            subject=subject,
            message_id=message_id,
            thread_id=result_thread_id,
            initiated_by=initiated_by,
            reason=reason,
            applicant_id=applicant_id
        )
        
        return {
            'message_id': message_id,
            'thread_id': result_thread_id
        }
        
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        raise


def modify_message(message_id: str, add_labels: List[str] = None, remove_labels: List[str] = None) -> bool:
    """
    Modify message labels.
    
    Args:
        message_id: Message ID
        add_labels: Labels to add
        remove_labels: Labels to remove
        
    Returns:
        True if successful
    """
    client = get_gmail_client()
    
    body = {}
    if add_labels:
        body['addLabelIds'] = add_labels
    if remove_labels:
        body['removeLabelIds'] = remove_labels
    
    try:
        client.service.users().messages().modify(
            userId='me',
            id=message_id,
            body=body
        ).execute()
        
        logger.info(f"Modified message {message_id} labels")
        return True
        
    except Exception as e:
        logger.error(f"Failed to modify message {message_id}: {str(e)}")
        return False


def get_message_body(message: dict) -> str:
    """
    Extract plain text body from a message.
    
    Args:
        message: Message dict from Gmail API
        
    Returns:
        Plain text body
    """
    def _get_body_from_part(part: dict) -> str:
        if part.get('mimeType') == 'text/plain':
            data = part['body'].get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')
        
        if 'parts' in part:
            for subpart in part['parts']:
                body = _get_body_from_part(subpart)
                if body:
                    return body
        
        return ''
    
    payload = message.get('payload', {})
    
    # Try to get body from top-level payload
    if payload.get('mimeType') == 'text/plain':
        data = payload['body'].get('data', '')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8')
    
    # Try to get from parts
    if 'parts' in payload:
        for part in payload['parts']:
            body = _get_body_from_part(part)
            if body:
                return body
    
    return ''


def get_message_headers(message: dict) -> Dict[str, str]:
    """
    Extract headers from a message.
    
    Args:
        message: Message dict from Gmail API
        
    Returns:
        Dict of header name -> value
    """
    headers = {}
    payload = message.get('payload', {})
    
    for header in payload.get('headers', []):
        headers[header['name']] = header['value']
    
    return headers

