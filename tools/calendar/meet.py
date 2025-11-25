"""
Google Meet integration helpers.
"""
from typing import Optional
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def extract_meet_link(event: dict) -> Optional[str]:
    """
    Extract Google Meet link from a calendar event.
    
    Args:
        event: Calendar event dict
        
    Returns:
        Meet link or None
    """
    if 'conferenceData' not in event:
        return None
    
    entry_points = event['conferenceData'].get('entryPoints', [])
    
    for entry_point in entry_points:
        if entry_point.get('entryPointType') == 'video':
            return entry_point.get('uri')
    
    return None


def get_meet_code(meet_link: str) -> Optional[str]:
    """
    Extract meeting code from a Meet link.
    
    Args:
        meet_link: Full Meet URL
        
    Returns:
        Meeting code or None
    """
    if not meet_link:
        return None
    
    # Extract code from URL like https://meet.google.com/abc-defg-hij
    parts = meet_link.split('/')
    if len(parts) > 0:
        return parts[-1]
    
    return None

