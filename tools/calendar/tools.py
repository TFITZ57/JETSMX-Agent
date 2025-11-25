"""
Calendar tools for Google ADK agents.
"""
from typing import Optional, List
from tools.calendar.events import (
    create_event as _create_event,
    get_event as _get_event,
    list_events as _list_events
)
from tools.calendar.freebusy import find_free_slots as _find_free_slots


def calendar_create_event(
    summary: str,
    start_time: str,
    end_time: str,
    attendees: Optional[List[str]] = None,
    description: Optional[str] = None,
    add_meet_link: bool = True,
    applicant_id: Optional[str] = None
) -> dict:
    """Create a calendar event with optional Google Meet link.
    
    Args:
        summary: Event title
        start_time: Start time in ISO 8601 format (e.g., '2024-01-15T10:00:00-05:00')
        end_time: End time in ISO 8601 format
        attendees: List of attendee email addresses
        description: Event description
        add_meet_link: Whether to add Google Meet conference
        applicant_id: Applicant ID for audit trail
        
    Returns:
        Event info with event_id, meet_link, html_link
    """
    return _create_event(
        summary=summary,
        start_time=start_time,
        end_time=end_time,
        attendees=attendees,
        description=description,
        conference=add_meet_link,
        applicant_id=applicant_id
    )


def calendar_get_event(event_id: str) -> Optional[dict]:
    """Get a calendar event by ID.
    
    Args:
        event_id: Event ID
        
    Returns:
        Event data or None
    """
    return _get_event(event_id)


def calendar_list_events(time_min: Optional[str] = None, time_max: Optional[str] = None) -> list:
    """List calendar events in a time range.
    
    Args:
        time_min: Start time in ISO 8601 format (defaults to now)
        time_max: End time in ISO 8601 format
        
    Returns:
        List of events
    """
    return _list_events(time_min=time_min, time_max=time_max)


def calendar_find_free_slots(duration_minutes: int, search_window_days: int = 7) -> list:
    """Find free time slots in the calendar.
    
    Args:
        duration_minutes: Duration of the desired slot
        search_window_days: How many days ahead to search
        
    Returns:
        List of free slots with start and end times
    """
    return _find_free_slots(
        duration_minutes=duration_minutes,
        search_window_days=search_window_days
    )


# Export all tools
ALL_CALENDAR_TOOLS = [
    calendar_create_event,
    calendar_get_event,
    calendar_list_events,
    calendar_find_free_slots
]

