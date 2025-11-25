"""
Gmail thread operations.
"""
from typing import Optional, List
from tools.gmail.client import get_gmail_client
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def get_thread(thread_id: str, format: str = 'full') -> Optional[dict]:
    """
    Get a thread by ID.
    
    Args:
        thread_id: Thread ID
        format: Response format (minimal, full, metadata)
        
    Returns:
        Thread data or None
    """
    client = get_gmail_client()
    
    try:
        thread = client.service.users().threads().get(
            userId='me',
            id=thread_id,
            format=format
        ).execute()
        return thread
    except Exception as e:
        logger.error(f"Failed to get thread {thread_id}: {str(e)}")
        return None


def list_threads(query: Optional[str] = None, label_ids: Optional[List[str]] = None, max_results: int = 100) -> List[dict]:
    """
    List threads matching criteria.
    
    Args:
        query: Gmail search query (e.g., 'from:user@example.com')
        label_ids: Filter by label IDs
        max_results: Maximum number of threads to return
        
    Returns:
        List of thread summaries
    """
    client = get_gmail_client()
    
    try:
        params = {
            'userId': 'me',
            'maxResults': max_results
        }
        
        if query:
            params['q'] = query
        if label_ids:
            params['labelIds'] = label_ids
        
        results = client.service.users().threads().list(**params).execute()
        threads = results.get('threads', [])
        
        logger.info(f"Listed {len(threads)} threads")
        return threads
        
    except Exception as e:
        logger.error(f"Failed to list threads: {str(e)}")
        return []


def modify_thread(thread_id: str, add_labels: List[str] = None, remove_labels: List[str] = None) -> bool:
    """
    Modify thread labels.
    
    Args:
        thread_id: Thread ID
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
        client.service.users().threads().modify(
            userId='me',
            id=thread_id,
            body=body
        ).execute()
        
        logger.info(f"Modified thread {thread_id} labels")
        return True
        
    except Exception as e:
        logger.error(f"Failed to modify thread {thread_id}: {str(e)}")
        return False

