"""
Calendar free/busy queries.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from tools.calendar.client import get_calendar_client
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def query_freebusy(
    calendars: List[str],
    time_min: str,
    time_max: str
) -> Dict[str, Any]:
    """
    Query free/busy information for calendars.
    
    Args:
        calendars: List of calendar IDs
        time_min: Start time (ISO 8601)
        time_max: End time (ISO 8601)
        
    Returns:
        Free/busy data
    """
    client = get_calendar_client()
    
    body = {
        'timeMin': time_min,
        'timeMax': time_max,
        'items': [{'id': cal_id} for cal_id in calendars]
    }
    
    try:
        freebusy = client.service.freebusy().query(body=body).execute()
        logger.info(f"Queried free/busy for {len(calendars)} calendars")
        return freebusy
    except Exception as e:
        logger.error(f"Failed to query free/busy: {str(e)}")
        return {}


def find_free_slots(
    duration_minutes: int,
    search_window_days: int = 7,
    calendar_id: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Find free time slots in a calendar.
    
    Args:
        duration_minutes: Duration of the desired slot
        search_window_days: How many days ahead to search
        calendar_id: Calendar ID
        
    Returns:
        List of free slots with start and end times
    """
    settings = get_settings()
    
    if calendar_id is None:
        calendar_id = settings.calendar_id
    
    # Query free/busy for the next N days
    time_min = datetime.utcnow()
    time_max = time_min + timedelta(days=search_window_days)
    
    freebusy_data = query_freebusy(
        calendars=[calendar_id],
        time_min=time_min.isoformat() + 'Z',
        time_max=time_max.isoformat() + 'Z'
    )
    
    if not freebusy_data or calendar_id not in freebusy_data.get('calendars', {}):
        return []
    
    busy_periods = freebusy_data['calendars'][calendar_id].get('busy', [])
    
    # Find gaps between busy periods
    free_slots = []
    current_time = time_min
    
    for busy in busy_periods:
        busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
        busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
        
        # Check if there's a gap before this busy period
        if (busy_start - current_time).total_seconds() >= duration_minutes * 60:
            free_slots.append({
                'start': current_time.isoformat(),
                'end': busy_start.isoformat()
            })
        
        current_time = max(current_time, busy_end)
    
    # Check if there's time remaining at the end
    if (time_max - current_time).total_seconds() >= duration_minutes * 60:
        free_slots.append({
            'start': current_time.isoformat(),
            'end': time_max.isoformat()
        })
    
    logger.info(f"Found {len(free_slots)} free slots")
    return free_slots

