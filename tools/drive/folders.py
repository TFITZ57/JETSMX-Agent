"""
Drive folder operations.
"""
from typing import List, Dict, Any, Optional
from tools.drive.client import get_drive_client
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def list_files_in_folder(folder_id: str, mime_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List files in a folder.
    
    Args:
        folder_id: Folder ID
        mime_type: Filter by MIME type (optional)
        
    Returns:
        List of file metadata
    """
    client = get_drive_client()
    
    query = f"'{folder_id}' in parents and trashed=false"
    
    if mime_type:
        query += f" and mimeType='{mime_type}'"
    
    try:
        results = client.service.files().list(
            q=query,
            fields='files(id,name,mimeType,createdTime,modifiedTime,webViewLink)',
            orderBy='createdTime desc'
        ).execute()
        
        files = results.get('files', [])
        logger.info(f"Listed {len(files)} files in folder {folder_id}")
        return files
        
    except Exception as e:
        logger.error(f"Failed to list files in folder {folder_id}: {str(e)}")
        return []


def create_folder(name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
    """
    Create a new folder.
    
    Args:
        name: Folder name
        parent_folder_id: Parent folder ID
        
    Returns:
        Folder ID or None
    """
    client = get_drive_client()
    
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]
    
    try:
        folder = client.service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        folder_id = folder['id']
        logger.info(f"Created folder: {folder_id} ({name})")
        return folder_id
        
    except Exception as e:
        logger.error(f"Failed to create folder {name}: {str(e)}")
        return None


def watch_folder(folder_id: str, webhook_url: str) -> Optional[Dict[str, Any]]:
    """
    Set up a watch on a folder for file changes.
    
    Args:
        folder_id: Folder ID to watch
        webhook_url: Webhook URL for notifications
        
    Returns:
        Watch channel info or None
    """
    client = get_drive_client()
    
    body = {
        'id': f'folder_watch_{folder_id}',
        'type': 'web_hook',
        'address': webhook_url
    }
    
    try:
        channel = client.service.files().watch(
            fileId=folder_id,
            body=body
        ).execute()
        
        logger.info(f"Set up watch on folder {folder_id}")
        return channel
        
    except Exception as e:
        logger.error(f"Failed to watch folder {folder_id}: {str(e)}")
        return None

