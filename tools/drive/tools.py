"""
Drive tools for Google ADK agents.
"""
from typing import Optional
from tools.drive.files import (
    get_file_metadata as _get_metadata,
    download_file as _download_file,
    upload_file as _upload_file
)
from tools.drive.folders import list_files_in_folder as _list_files


def drive_get_file_metadata(file_id: str) -> Optional[dict]:
    """Get Drive file metadata.
    
    Args:
        file_id: Drive file ID
        
    Returns:
        File metadata including name, MIME type, created time, web link
    """
    return _get_metadata(file_id)


def drive_download_file(file_id: str) -> Optional[bytes]:
    """Download a file from Drive.
    
    Args:
        file_id: Drive file ID
        
    Returns:
        File content as bytes or None
    """
    return _download_file(file_id)


def drive_upload_file(name: str, content: bytes, mime_type: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
    """Upload a file to Drive.
    
    Args:
        name: File name
        content: File content as bytes
        mime_type: MIME type (e.g., 'application/pdf', 'text/plain')
        parent_folder_id: Parent folder ID (optional)
        
    Returns:
        File ID of uploaded file or None
    """
    return _upload_file(name, content, mime_type, parent_folder_id)


def drive_list_files_in_folder(folder_id: str, mime_type: Optional[str] = None) -> list:
    """List files in a Drive folder.
    
    Args:
        folder_id: Folder ID
        mime_type: Filter by MIME type (optional, e.g., 'application/pdf')
        
    Returns:
        List of file metadata
    """
    return _list_files(folder_id, mime_type)


# Export all tools
ALL_DRIVE_TOOLS = [
    drive_get_file_metadata,
    drive_download_file,
    drive_upload_file,
    drive_list_files_in_folder
]

