"""
Calendar event operations.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from tools.calendar.client import get_calendar_client
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger
from shared.logging.audit import log_calendar_event_created

logger = setup_logger(__name__)


def create_event(
    summary: str,
    start_time: str,
    end_time: str,
    attendees: Optional[List[str]] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    calendar_id: Optional[str] = None,
    conference: bool = True,
    agent_name: str = "hr_pipeline_agent",
    applicant_id: Optional[str] = None
) -> dict:
    """
    Create a calendar event.
    
    Args:
        summary: Event title
        start_time: Start time (ISO 8601 format)
        end_time: End time (ISO 8601 format)
        attendees: List of attendee emails
        description: Event description
        location: Event location
        calendar_id: Calendar ID (uses settings default if not provided)
        conference: Whether to add Google Meet conference
        agent_name: Agent creating the event
        applicant_id: Applicant ID for audit
        
    Returns:
        Event info with event_id, meet_link, etc.
    """
    client = get_calendar_client()
    settings = get_settings()
    
    if calendar_id is None:
        calendar_id = settings.calendar_id
    
    event_body = {
        'summary': summary,
        'start': {
            'dateTime': start_time,
            'timeZone': 'America/New_York'
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'America/New_York'
        }
    }
    
    if description:
        event_body['description'] = description
    
    if location:
        event_body['location'] = location
    
    if attendees:
        event_body['attendees'] = [{'email': email} for email in attendees]
    
    if conference:
        event_body['conferenceData'] = {
            'createRequest': {
                'requestId': f'event_{datetime.utcnow().timestamp()}',
                'conferenceSolutionKey': {'type': 'hangoutsMeet'}
            }
        }
    
    try:
        event = client.service.events().insert(
            calendarId=calendar_id,
            body=event_body,
            conferenceDataVersion=1 if conference else 0
        ).execute()
        
        event_id = event['id']
        meet_link = None
        
        if 'conferenceData' in event:
            meet_link = event['conferenceData'].get('entryPoints', [{}])[0].get('uri')
        
        logger.info(f"Created calendar event: {event_id}")
        
        # Audit log
        log_calendar_event_created(
            event_id=event_id,
            summary=summary,
            start_time=start_time,
            attendees=attendees or [],
            agent_name=agent_name,
            applicant_id=applicant_id
        )
        
        return {
            'event_id': event_id,
            'summary': summary,
            'start_time': start_time,
            'end_time': end_time,
            'meet_link': meet_link,
            'html_link': event.get('htmlLink')
        }
        
    except Exception as e:
        logger.error(f"Failed to create calendar event: {str(e)}")
        raise


def get_event(event_id: str, calendar_id: Optional[str] = None) -> Optional[dict]:
    """
    Get a calendar event.
    
    Args:
        event_id: Event ID
        calendar_id: Calendar ID
        
    Returns:
        Event data or None
    """
    client = get_calendar_client()
    settings = get_settings()
    
    if calendar_id is None:
        calendar_id = settings.calendar_id
    
    try:
        event = client.service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        return event
    except Exception as e:
        logger.error(f"Failed to get event {event_id}: {str(e)}")
        return None


def update_event(event_id: str, updates: Dict[str, Any], calendar_id: Optional[str] = None) -> bool:
    """
    Update a calendar event.
    
    Args:
        event_id: Event ID
        updates: Fields to update
        calendar_id: Calendar ID
        
    Returns:
        True if successful
    """
    client = get_calendar_client()
    settings = get_settings()
    
    if calendar_id is None:
        calendar_id = settings.calendar_id
    
    try:
        # Get current event
        event = client.service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        # Apply updates
        event.update(updates)
        
        # Update event
        client.service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event
        ).execute()
        
        logger.info(f"Updated calendar event: {event_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update event {event_id}: {str(e)}")
        return False


def delete_event(event_id: str, calendar_id: Optional[str] = None) -> bool:
    """
    Delete a calendar event.
    
    Args:
        event_id: Event ID
        calendar_id: Calendar ID
        
    Returns:
        True if successful
    """
    client = get_calendar_client()
    settings = get_settings()
    
    if calendar_id is None:
        calendar_id = settings.calendar_id
    
    try:
        client.service.events().delete(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()
        
        logger.info(f"Deleted calendar event: {event_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete event {event_id}: {str(e)}")
        return False


def list_events(
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    calendar_id: Optional[str] = None,
    max_results: int = 100
) -> List[dict]:
    """
    List calendar events in a time range.
    
    Args:
        time_min: Start time (ISO 8601)
        time_max: End time (ISO 8601)
        calendar_id: Calendar ID
        max_results: Maximum events to return
        
    Returns:
        List of events
    """
    client = get_calendar_client()
    settings = get_settings()
    
    if calendar_id is None:
        calendar_id = settings.calendar_id
    
    if time_min is None:
        time_min = datetime.utcnow().isoformat() + 'Z'
    
    try:
        params = {
            'calendarId': calendar_id,
            'timeMin': time_min,
            'maxResults': max_results,
            'singleEvents': True,
            'orderBy': 'startTime'
        }
        
        if time_max:
            params['timeMax'] = time_max
        
        events_result = client.service.events().list(**params).execute()
        events = events_result.get('items', [])
        
        logger.info(f"Listed {len(events)} calendar events")
        return events
        
    except Exception as e:
        logger.error(f"Failed to list events: {str(e)}")
        return []

