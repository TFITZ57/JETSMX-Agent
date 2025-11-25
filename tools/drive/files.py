"""
Drive file operations.
"""
from typing import Optional, Dict, Any
import io
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from tools.drive.client import get_drive_client
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def get_file_metadata(file_id: str) -> Optional[Dict[str, Any]]:
    """
    Get file metadata.
    
    Args:
        file_id: Drive file ID
        
    Returns:
        File metadata or None
    """
    client = get_drive_client()
    
    try:
        file = client.service.files().get(
            fileId=file_id,
            fields='id,name,mimeType,parents,createdTime,modifiedTime,webViewLink,size'
        ).execute()
        return file
    except Exception as e:
        logger.error(f"Failed to get file metadata for {file_id}: {str(e)}")
        return None


def download_file(file_id: str) -> Optional[bytes]:
    """
    Download file content.
    
    Args:
        file_id: Drive file ID
        
    Returns:
        File content as bytes or None
    """
    client = get_drive_client()
    
    try:
        request = client.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.debug(f"Download progress: {int(status.progress() * 100)}%")
        
        fh.seek(0)
        content = fh.read()
        
        logger.info(f"Downloaded file {file_id}, size: {len(content)} bytes")
        return content
        
    except Exception as e:
        logger.error(f"Failed to download file {file_id}: {str(e)}")
        return None


def upload_file(
    name: str,
    content: bytes,
    mime_type: str,
    parent_folder_id: Optional[str] = None
) -> Optional[str]:
    """
    Upload a file to Drive.
    
    Args:
        name: File name
        content: File content as bytes
        mime_type: MIME type
        parent_folder_id: Parent folder ID
        
    Returns:
        File ID or None
    """
    client = get_drive_client()
    
    file_metadata = {'name': name}
    
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]
    
    try:
        fh = io.BytesIO(content)
        media = MediaIoBaseUpload(fh, mimetype=mime_type, resumable=True)
        
        file = client.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,webViewLink'
        ).execute()
        
        file_id = file['id']
        logger.info(f"Uploaded file: {file_id} ({name})")
        return file_id
        
    except Exception as e:
        logger.error(f"Failed to upload file {name}: {str(e)}")
        return None


def move_file(file_id: str, new_parent_id: str) -> bool:
    """
    Move a file to a different folder.
    
    Args:
        file_id: File ID
        new_parent_id: New parent folder ID
        
    Returns:
        True if successful
    """
    client = get_drive_client()
    
    try:
        # Get current parents
        file = client.service.files().get(
            fileId=file_id,
            fields='parents'
        ).execute()
        
        previous_parents = ','.join(file.get('parents', []))
        
        # Move file
        client.service.files().update(
            fileId=file_id,
            addParents=new_parent_id,
            removeParents=previous_parents,
            fields='id,parents'
        ).execute()
        
        logger.info(f"Moved file {file_id} to folder {new_parent_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to move file {file_id}: {str(e)}")
        return False


def delete_file(file_id: str) -> bool:
    """
    Delete a file.
    
    Args:
        file_id: File ID
        
    Returns:
        True if successful
    """
    client = get_drive_client()
    
    try:
        client.service.files().delete(fileId=file_id).execute()
        logger.info(f"Deleted file {file_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {str(e)}")
        return False

