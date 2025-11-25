"""
Drive permissions and sharing operations.
"""
from typing import Optional, Dict, Any
from tools.drive.client import get_drive_client
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def share_file(
    file_id: str,
    email: str,
    role: str = 'reader',
    notify: bool = False
) -> bool:
    """
    Share a file with a user.
    
    Args:
        file_id: File ID
        email: Email to share with
        role: Permission role (reader, writer, commenter, owner)
        notify: Whether to send notification email
        
    Returns:
        True if successful
    """
    client = get_drive_client()
    
    permission = {
        'type': 'user',
        'role': role,
        'emailAddress': email
    }
    
    try:
        client.service.permissions().create(
            fileId=file_id,
            body=permission,
            sendNotificationEmail=notify,
            fields='id'
        ).execute()
        
        logger.info(f"Shared file {file_id} with {email} as {role}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to share file {file_id}: {str(e)}")
        return False


def make_file_public(file_id: str) -> Optional[str]:
    """
    Make a file publicly viewable.
    
    Args:
        file_id: File ID
        
    Returns:
        Web view link or None
    """
    client = get_drive_client()
    
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    
    try:
        client.service.permissions().create(
            fileId=file_id,
            body=permission,
            fields='id'
        ).execute()
        
        # Get web view link
        file = client.service.files().get(
            fileId=file_id,
            fields='webViewLink'
        ).execute()
        
        web_link = file.get('webViewLink')
        logger.info(f"Made file {file_id} public: {web_link}")
        return web_link
        
    except Exception as e:
        logger.error(f"Failed to make file {file_id} public: {str(e)}")
        return None

