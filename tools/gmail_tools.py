"""
Gmail API wrapper tools for JetsMX Agent Framework.

Provides typed, retry-enabled functions for interacting with Gmail:
messages, threads, drafts, labels, and push notifications.
All functions include structured logging and error handling.
"""
from typing import Dict, List, Optional, Any
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import mimetypes
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from shared.config.settings import get_settings
from shared.config.constants import GMAIL_SCOPES, MAX_RETRIES, RETRY_BACKOFF_FACTOR, RETRY_MIN_WAIT, RETRY_MAX_WAIT
from shared.auth.google_auth import get_delegated_credentials
from shared.logging.logger import setup_logger, log_with_context

logger = setup_logger(__name__)
settings = get_settings()

# Retry policy for transient failures and rate limits
retry_policy = retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=RETRY_BACKOFF_FACTOR, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    retry=retry_if_exception_type((HttpError, TimeoutError))
)


def _get_gmail_service(user_email: Optional[str] = None) -> Resource:
    """
    Get Gmail API service instance with delegated credentials.
    
    Args:
        user_email: Email to impersonate. If None, uses default from settings.
        
    Returns:
        Gmail API service resource
    """
    user_email = user_email or settings.gmail_user_email
    credentials = get_delegated_credentials(user_email, GMAIL_SCOPES)
    return build('gmail', 'v1', credentials=credentials)


def _create_message(
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    html: bool = False
) -> Dict[str, str]:
    """
    Create a MIME message suitable for Gmail API.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text or HTML)
        from_email: Sender email. If None, uses default from settings.
        cc: List of CC email addresses
        bcc: List of BCC email addresses
        attachments: List of dicts with 'filename' and 'content' (bytes) keys
        html: If True, body is treated as HTML
        
    Returns:
        Dict with 'raw' key containing base64-encoded message
    """
    from_email = from_email or settings.gmail_user_email
    
    # Create message container
    if attachments:
        message = MIMEMultipart()
    else:
        message = MIMEText(body, 'html' if html else 'plain')
    
    message['To'] = to
    message['From'] = from_email
    message['Subject'] = subject
    
    if cc:
        message['Cc'] = ', '.join(cc)
    if bcc:
        message['Bcc'] = ', '.join(bcc)
    
    # Add body if multipart
    if attachments:
        body_part = MIMEText(body, 'html' if html else 'plain')
        message.attach(body_part)
        
        # Add attachments
        for attachment in attachments:
            filename = attachment['filename']
            content = attachment['content']
            
            # Guess MIME type
            content_type, _ = mimetypes.guess_type(filename)
            if content_type is None:
                content_type = 'application/octet-stream'
            
            main_type, sub_type = content_type.split('/', 1)
            
            part = MIMEBase(main_type, sub_type)
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            message.attach(part)
    
    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}


def _decode_message_body(message: Dict[str, Any]) -> str:
    """
    Extract plain text body from Gmail message payload.
    
    Args:
        message: Gmail message resource
        
    Returns:
        Decoded message body text
    """
    payload = message.get('payload', {})
    
    # Handle simple plain text messages
    if payload.get('mimeType') == 'text/plain' and 'body' in payload:
        data = payload['body'].get('data', '')
        if data:
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    
    # Handle multipart messages
    parts = payload.get('parts', [])
    for part in parts:
        mime_type = part.get('mimeType', '')
        
        # Prefer text/plain over text/html
        if mime_type == 'text/plain' and 'body' in part:
            data = part['body'].get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    
    # Fall back to text/html
    for part in parts:
        mime_type = part.get('mimeType', '')
        if mime_type == 'text/html' and 'body' in part:
            data = part['body'].get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    
    # Recursively search nested parts
    for part in parts:
        if 'parts' in part:
            nested_body = _decode_message_body({'payload': part})
            if nested_body:
                return nested_body
    
    return ""


@retry_policy
def list_threads(
    query: Optional[str] = None,
    label_ids: Optional[List[str]] = None,
    max_results: int = 100,
    user_email: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List Gmail threads matching query and label filters.
    
    Args:
        query: Gmail search query (e.g., "from:jobs@jetstreammx.com is:unread")
        label_ids: List of label IDs to filter by (e.g., ["INBOX", "UNREAD"])
        max_results: Maximum number of threads to return (default: 100)
        user_email: Email to access. If None, uses default from settings.
        
    Returns:
        List of thread dicts with 'id', 'snippet', and message metadata
        
    Raises:
        HttpError: If API call fails after retries
    """
    try:
        service = _get_gmail_service(user_email)
        
        # Build request parameters
        request_params = {'userId': 'me', 'maxResults': max_results}
        if query:
            request_params['q'] = query
        if label_ids:
            request_params['labelIds'] = label_ids
        
        response = service.users().threads().list(**request_params).execute()
        threads = response.get('threads', [])
        
        # Enrich with thread details
        result = []
        for thread in threads:
            thread_id = thread['id']
            thread_detail = service.users().threads().get(userId='me', id=thread_id).execute()
            
            messages = thread_detail.get('messages', [])
            first_message = messages[0] if messages else {}
            headers = {h['name']: h['value'] for h in first_message.get('payload', {}).get('headers', [])}
            
            result.append({
                'id': thread_id,
                'snippet': thread_detail.get('snippet', ''),
                'message_count': len(messages),
                'subject': headers.get('Subject', ''),
                'from': headers.get('From', ''),
                'to': headers.get('To', ''),
                'date': headers.get('Date', '')
            })
        
        log_with_context(
            logger, "info", "Listed Gmail threads",
            query=query,
            label_ids=label_ids,
            count=len(result),
            user_email=user_email or settings.gmail_user_email
        )
        
        return result
        
    except HttpError as e:
        log_with_context(
            logger, "error", "Failed to list Gmail threads",
            query=query,
            label_ids=label_ids,
            error=str(e),
            status_code=e.resp.status if hasattr(e, 'resp') else None
        )
        raise
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to list Gmail threads",
            query=query,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


@retry_policy
def get_message(
    message_id: str,
    user_email: Optional[str] = None,
    format: str = 'full'
) -> Dict[str, Any]:
    """
    Fetch a Gmail message by ID with full details.
    
    Args:
        message_id: Gmail message ID
        user_email: Email to access. If None, uses default from settings.
        format: Message format ('full', 'metadata', 'minimal', 'raw')
        
    Returns:
        Message dict with id, threadId, labelIds, snippet, payload, headers, and body
        
    Raises:
        HttpError: If message not found or API call fails
    """
    try:
        service = _get_gmail_service(user_email)
        
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format=format
        ).execute()
        
        # Extract headers
        headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
        
        # Decode body
        body = _decode_message_body(message) if format == 'full' else ""
        
        result = {
            'id': message['id'],
            'threadId': message.get('threadId', ''),
            'labelIds': message.get('labelIds', []),
            'snippet': message.get('snippet', ''),
            'internalDate': message.get('internalDate', ''),
            'subject': headers.get('Subject', ''),
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'cc': headers.get('Cc', ''),
            'date': headers.get('Date', ''),
            'body': body
        }
        
        log_with_context(
            logger, "info", "Fetched Gmail message",
            message_id=message_id,
            thread_id=result['threadId'],
            subject=result['subject'][:50],
            user_email=user_email or settings.gmail_user_email
        )
        
        return result
        
    except HttpError as e:
        log_with_context(
            logger, "error", "Failed to fetch Gmail message",
            message_id=message_id,
            error=str(e),
            status_code=e.resp.status if hasattr(e, 'resp') else None
        )
        raise
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to fetch Gmail message",
            message_id=message_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


@retry_policy
def create_draft(
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    html: bool = False,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a draft email in Gmail.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text or HTML)
        from_email: Sender email. If None, uses default from settings.
        cc: List of CC email addresses
        bcc: List of BCC email addresses
        attachments: List of dicts with 'filename' and 'content' (bytes) keys
        html: If True, body is treated as HTML
        user_email: Email to access. If None, uses default from settings.
        
    Returns:
        Draft dict with 'id' and 'message' keys
        
    Raises:
        HttpError: If draft creation fails
    """
    try:
        service = _get_gmail_service(user_email)
        
        message = _create_message(
            to=to,
            subject=subject,
            body=body,
            from_email=from_email,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            html=html
        )
        
        draft = service.users().drafts().create(
            userId='me',
            body={'message': message}
        ).execute()
        
        result = {
            'id': draft['id'],
            'message': {
                'id': draft['message']['id'],
                'threadId': draft['message'].get('threadId', '')
            }
        }
        
        log_with_context(
            logger, "info", "Created Gmail draft",
            draft_id=result['id'],
            to=to,
            subject=subject,
            has_attachments=bool(attachments),
            user_email=user_email or settings.gmail_user_email
        )
        
        return result
        
    except HttpError as e:
        log_with_context(
            logger, "error", "Failed to create Gmail draft",
            to=to,
            subject=subject,
            error=str(e),
            status_code=e.resp.status if hasattr(e, 'resp') else None
        )
        raise
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to create Gmail draft",
            to=to,
            subject=subject,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


@retry_policy
def send_message(
    draft_id: Optional[str] = None,
    raw: Optional[str] = None,
    to: Optional[str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    from_email: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    html: bool = False,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send an email via Gmail. Can send from draft or create new message.
    
    Args:
        draft_id: Draft ID to send (if sending existing draft)
        raw: Raw base64-encoded message (if sending pre-formatted message)
        to: Recipient (if creating new message)
        subject: Subject (if creating new message)
        body: Body (if creating new message)
        from_email: Sender email
        cc: CC recipients
        bcc: BCC recipients
        attachments: Attachments list
        html: If True, body is HTML
        user_email: Email to access. If None, uses default from settings.
        
    Returns:
        Sent message dict with 'id', 'threadId', and 'labelIds'
        
    Raises:
        HttpError: If send fails
        ValueError: If neither draft_id nor message parameters provided
    """
    try:
        service = _get_gmail_service(user_email)
        
        if draft_id:
            # Send existing draft
            result = service.users().drafts().send(
                userId='me',
                body={'id': draft_id}
            ).execute()
            
            log_with_context(
                logger, "info", "Sent Gmail draft",
                draft_id=draft_id,
                message_id=result['id'],
                thread_id=result.get('threadId', ''),
                user_email=user_email or settings.gmail_user_email
            )
            
        elif raw:
            # Send raw message
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            log_with_context(
                logger, "info", "Sent raw Gmail message",
                message_id=result['id'],
                thread_id=result.get('threadId', ''),
                user_email=user_email or settings.gmail_user_email
            )
            
        elif to and subject and body:
            # Create and send new message
            message = _create_message(
                to=to,
                subject=subject,
                body=body,
                from_email=from_email,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                html=html
            )
            
            result = service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            log_with_context(
                logger, "info", "Sent new Gmail message",
                to=to,
                subject=subject,
                message_id=result['id'],
                thread_id=result.get('threadId', ''),
                user_email=user_email or settings.gmail_user_email
            )
            
        else:
            raise ValueError("Must provide either draft_id, raw message, or to/subject/body parameters")
        
        return {
            'id': result['id'],
            'threadId': result.get('threadId', ''),
            'labelIds': result.get('labelIds', [])
        }
        
    except HttpError as e:
        log_with_context(
            logger, "error", "Failed to send Gmail message",
            draft_id=draft_id,
            to=to,
            error=str(e),
            status_code=e.resp.status if hasattr(e, 'resp') else None
        )
        raise
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to send Gmail message",
            draft_id=draft_id,
            to=to,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


@retry_policy
def modify_message(
    message_id: str,
    add_labels: Optional[List[str]] = None,
    remove_labels: Optional[List[str]] = None,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Modify labels on a Gmail message.
    
    Args:
        message_id: Message ID to modify
        add_labels: List of label IDs to add (e.g., ["STARRED", "IMPORTANT"])
        remove_labels: List of label IDs to remove (e.g., ["UNREAD", "INBOX"])
        user_email: Email to access. If None, uses default from settings.
        
    Returns:
        Modified message dict with 'id', 'threadId', and 'labelIds'
        
    Raises:
        HttpError: If modification fails
    """
    try:
        service = _get_gmail_service(user_email)
        
        body = {}
        if add_labels:
            body['addLabelIds'] = add_labels
        if remove_labels:
            body['removeLabelIds'] = remove_labels
        
        if not body:
            raise ValueError("Must provide either add_labels or remove_labels")
        
        result = service.users().messages().modify(
            userId='me',
            id=message_id,
            body=body
        ).execute()
        
        log_with_context(
            logger, "info", "Modified Gmail message labels",
            message_id=message_id,
            add_labels=add_labels,
            remove_labels=remove_labels,
            user_email=user_email or settings.gmail_user_email
        )
        
        return {
            'id': result['id'],
            'threadId': result.get('threadId', ''),
            'labelIds': result.get('labelIds', [])
        }
        
    except HttpError as e:
        log_with_context(
            logger, "error", "Failed to modify Gmail message",
            message_id=message_id,
            add_labels=add_labels,
            remove_labels=remove_labels,
            error=str(e),
            status_code=e.resp.status if hasattr(e, 'resp') else None
        )
        raise
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to modify Gmail message",
            message_id=message_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


@retry_policy
def watch(
    topic: str,
    label_ids: Optional[List[str]] = None,
    user_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Set up Gmail push notifications to a Cloud Pub/Sub topic.
    
    This enables real-time notifications when messages arrive or labels change.
    Watch expires after 7 days and must be renewed.
    
    Args:
        topic: Full Pub/Sub topic name (e.g., "projects/PROJECT_ID/topics/TOPIC_NAME")
        label_ids: List of label IDs to watch (e.g., ["INBOX"]). If None, watches all.
        user_email: Email to watch. If None, uses default from settings.
        
    Returns:
        Watch response dict with 'historyId' and 'expiration' (Unix timestamp in ms)
        
    Raises:
        HttpError: If watch setup fails
        
    Note:
        The service account must have permission to publish to the Pub/Sub topic.
    """
    try:
        service = _get_gmail_service(user_email)
        
        body = {'topicName': topic}
        if label_ids:
            body['labelIds'] = label_ids
        
        result = service.users().watch(userId='me', body=body).execute()
        
        log_with_context(
            logger, "info", "Set up Gmail watch",
            topic=topic,
            label_ids=label_ids,
            history_id=result.get('historyId', ''),
            expiration=result.get('expiration', ''),
            user_email=user_email or settings.gmail_user_email
        )
        
        return {
            'historyId': result.get('historyId', ''),
            'expiration': result.get('expiration', '')
        }
        
    except HttpError as e:
        log_with_context(
            logger, "error", "Failed to set up Gmail watch",
            topic=topic,
            label_ids=label_ids,
            error=str(e),
            status_code=e.resp.status if hasattr(e, 'resp') else None
        )
        raise
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to set up Gmail watch",
            topic=topic,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


@retry_policy
def stop_watch(user_email: Optional[str] = None) -> None:
    """
    Stop Gmail push notifications.
    
    Args:
        user_email: Email to stop watching. If None, uses default from settings.
        
    Raises:
        HttpError: If stop fails
    """
    try:
        service = _get_gmail_service(user_email)
        service.users().stop(userId='me').execute()
        
        log_with_context(
            logger, "info", "Stopped Gmail watch",
            user_email=user_email or settings.gmail_user_email
        )
        
    except HttpError as e:
        log_with_context(
            logger, "error", "Failed to stop Gmail watch",
            error=str(e),
            status_code=e.resp.status if hasattr(e, 'resp') else None
        )
        raise
    except Exception as e:
        log_with_context(
            logger, "error", "Failed to stop Gmail watch",
            error=str(e),
            error_type=type(e).__name__
        )
        raise

