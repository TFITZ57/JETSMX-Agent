"""
Gmail Pub/Sub handler for processing email notifications.
"""
from typing import Dict, Any, List, Optional
from tools.gmail.client import get_gmail_client
from tools.gmail.messages import get_message, get_message_body, get_message_headers
from tools.airtable.pipeline import find_pipeline_by_thread_id
from agents.hr_pipeline.agent import get_hr_pipeline_agent
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def get_history_messages(history_id: str, start_history_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch messages from Gmail history.
    
    Args:
        history_id: Current history ID from Pub/Sub notification
        start_history_id: Previous history ID to start from
        
    Returns:
        List of new messages
    """
    client = get_gmail_client()
    
    try:
        # If no start_history_id, just return empty (need to track this in production)
        if not start_history_id:
            logger.warning("No start_history_id provided, cannot fetch history")
            return []
        
        history = client.service.users().history().list(
            userId='me',
            startHistoryId=start_history_id,
            historyTypes=['messageAdded']
        ).execute()
        
        messages = []
        if 'history' in history:
            for record in history['history']:
                if 'messagesAdded' in record:
                    for msg_added in record['messagesAdded']:
                        messages.append(msg_added['message'])
        
        logger.info(f"Fetched {len(messages)} messages from history")
        return messages
        
    except Exception as e:
        logger.error(f"Failed to fetch history: {str(e)}")
        return []


def extract_thread_messages(thread_id: str) -> List[Dict[str, Any]]:
    """
    Get all messages in a thread.
    
    Args:
        thread_id: Gmail thread ID
        
    Returns:
        List of messages in thread
    """
    from tools.gmail.threads import get_thread
    
    try:
        thread = get_thread(thread_id, format='full')
        if thread and 'messages' in thread:
            return thread['messages']
        return []
    except Exception as e:
        logger.error(f"Failed to get thread {thread_id}: {str(e)}")
        return []


def is_reply_from_applicant(message: Dict[str, Any], applicant_email: str) -> bool:
    """
    Check if message is a reply from the applicant.
    
    Args:
        message: Gmail message object
        applicant_email: Expected applicant email
        
    Returns:
        True if message is from applicant
    """
    headers = get_message_headers(message)
    from_header = headers.get('From', '').lower()
    
    return applicant_email.lower() in from_header


def handle_gmail_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle Gmail Pub/Sub notification.
    
    Args:
        event_data: Gmail push notification payload with history_id
        
    Returns:
        Processing result
    """
    history_id = event_data.get('history_id')
    email_address = event_data.get('email_address', 'me')
    
    logger.info(f"Processing Gmail notification: history_id={history_id}")
    
    try:
        # In production, you'd track the last_history_id per account
        # For now, we'll use a simpler approach: check recent threads
        
        # Get the message_id if provided directly (simpler path for testing)
        message_id = event_data.get('message_id')
        thread_id = event_data.get('thread_id')
        
        if message_id:
            # Direct message processing (for testing/webhook scenarios)
            return process_message_direct(message_id, thread_id)
        
        # For Pub/Sub watch notifications, we'd fetch history
        # For MVP, return a note about needing history tracking
        logger.info("Pub/Sub watch notification received, history tracking needed for production")
        
        return {
            "status": "history_tracking_needed",
            "history_id": history_id,
            "note": "Implement history tracking for production"
        }
        
    except Exception as e:
        logger.error(f"Error handling Gmail event: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "history_id": history_id
        }


def process_message_direct(message_id: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a specific message directly.
    
    Args:
        message_id: Gmail message ID
        thread_id: Gmail thread ID (optional, will be fetched from message)
        
    Returns:
        Processing result
    """
    logger.info(f"Processing message directly: {message_id}")
    
    try:
        # Fetch the message
        message = get_message(message_id, format='full')
        if not message:
            return {"status": "error", "error": "Message not found"}
        
        # Get thread_id from message if not provided
        if not thread_id:
            thread_id = message.get('threadId')
        
        # Check if this thread is associated with a pipeline
        pipeline = find_pipeline_by_thread_id(thread_id)
        
        if not pipeline:
            logger.info(f"Thread {thread_id} not associated with any pipeline")
            return {
                "status": "ignored",
                "reason": "Thread not associated with pipeline",
                "thread_id": thread_id
            }
        
        # Extract message details
        headers = get_message_headers(message)
        from_email = headers.get('From', '')
        subject = headers.get('Subject', '')
        body_text = get_message_body(message)
        
        # Check if this is from the applicant
        if not is_reply_from_applicant(message, pipeline.primary_email):
            logger.info(f"Message not from applicant {pipeline.primary_email}")
            return {
                "status": "ignored",
                "reason": "Message not from applicant",
                "from": from_email
            }
        
        logger.info(f"Processing applicant reply from {pipeline.applicant_name}")
        
        # Invoke HR Pipeline agent
        hr_agent = get_hr_pipeline_agent()
        result = hr_agent.parse_applicant_email_reply(
            thread_id=thread_id,
            message_id=message_id,
            body_text=body_text,
            pipeline_id=pipeline.id
        )
        
        return {
            "status": "processed",
            "pipeline_id": pipeline.id,
            "applicant_name": pipeline.applicant_name,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error processing message {message_id}: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "message_id": message_id
        }

