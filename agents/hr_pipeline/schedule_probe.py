"""
Probe call scheduling coordinator.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from tools.calendar.events import create_event
from tools.airtable.pipeline import update_pipeline_record, get_pipeline_record
from shared.models.pipeline import PipelineUpdate
from shared.logging.logger import setup_logger
from shared.config.settings import get_settings

logger = setup_logger(__name__)


def format_probe_call_description(applicant_name: str, phone: str, pipeline_id: str) -> str:
    """
    Format the description for a probe call event.
    
    Args:
        applicant_name: Applicant's name
        phone: Phone number
        pipeline_id: Pipeline record ID
        
    Returns:
        Formatted description
    """
    description = f"""Phone Probe Call with {applicant_name}

Contact: {phone}

This is an initial screening call to discuss:
- Aviation experience and background
- A&P license details
- On-call availability and constraints
- Geographic flexibility
- Compensation expectations

Pipeline ID: {pipeline_id}

Prepare to update Airtable with notes after the call.
"""
    return description


def schedule_probe_call(
    pipeline_id: str,
    start_time: str,
    end_time: str,
    phone_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Schedule a probe call event and update Airtable.
    
    Args:
        pipeline_id: Pipeline record ID
        start_time: Event start time (ISO 8601 format)
        end_time: Event end time (ISO 8601 format)
        phone_number: Applicant phone number (optional, will fetch from pipeline)
        
    Returns:
        Result dict with event details
    """
    logger.info(f"Scheduling probe call for pipeline {pipeline_id}")
    
    try:
        # Get pipeline record to get applicant info
        pipeline = get_pipeline_record(pipeline_id)
        if not pipeline:
            return {
                'success': False,
                'error': 'Pipeline record not found'
            }
        
        # Use confirmed phone number if not provided
        if not phone_number:
            phone_number = pipeline.confirmed_phone_number or "Phone TBD"
        
        applicant_name = pipeline.applicant_name or "Applicant"
        applicant_email = pipeline.primary_email
        
        # Create calendar event
        event_summary = f"Probe Call - {applicant_name}"
        event_description = format_probe_call_description(
            applicant_name=applicant_name,
            phone=phone_number,
            pipeline_id=pipeline_id
        )
        
        # Add applicant as attendee if we have their email
        attendees = []
        if applicant_email:
            attendees.append(applicant_email)
        
        # Create the event with Google Meet
        event_result = create_event(
            summary=event_summary,
            start_time=start_time,
            end_time=end_time,
            attendees=attendees,
            description=event_description,
            conference=True,
            agent_name="hr_pipeline_agent",
            applicant_id=pipeline.applicant
        )
        
        event_id = event_result['event_id']
        meet_link = event_result.get('meet_link')
        
        logger.info(f"Created calendar event {event_id} with Meet link: {meet_link}")
        
        # Update Airtable pipeline record
        update_data = PipelineUpdate(
            probe_call_event_id=event_id,
            probe_call_datetime=datetime.fromisoformat(start_time.replace('Z', '+00:00')),
            probe_call_meet_link=meet_link,
            pipeline_stage="Phone Probe Scheduled",
            probe_chat_notified=True  # We'll notify in Chat after this
        )
        
        update_success = update_pipeline_record(
            pipeline_id,
            update_data,
            agent_name="hr_pipeline_agent"
        )
        
        if not update_success:
            logger.error("Failed to update pipeline record after creating event")
            # Event was created, but Airtable update failed
            # In production, might want to implement cleanup/retry logic
        
        return {
            'success': True,
            'event_id': event_id,
            'meet_link': meet_link,
            'start_time': start_time,
            'end_time': end_time,
            'applicant_name': applicant_name,
            'pipeline_id': pipeline_id
        }
        
    except Exception as e:
        logger.error(f"Failed to schedule probe call: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'pipeline_id': pipeline_id
        }


def cancel_probe_call(pipeline_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Cancel a scheduled probe call.
    
    Args:
        pipeline_id: Pipeline record ID
        reason: Reason for cancellation
        
    Returns:
        Result dict
    """
    logger.info(f"Cancelling probe call for pipeline {pipeline_id}")
    
    try:
        pipeline = get_pipeline_record(pipeline_id)
        if not pipeline:
            return {'success': False, 'error': 'Pipeline not found'}
        
        event_id = pipeline.probe_call_event_id
        if not event_id:
            return {'success': False, 'error': 'No probe call event to cancel'}
        
        # Delete calendar event
        from tools.calendar.events import delete_event
        delete_success = delete_event(event_id)
        
        if not delete_success:
            logger.warning(f"Failed to delete calendar event {event_id}")
        
        # Update pipeline
        update_data = PipelineUpdate(
            probe_call_event_id=None,
            probe_call_datetime=None,
            probe_call_meet_link=None,
            pipeline_stage="Applicant Responded",
            screening_notes=f"Probe call cancelled. Reason: {reason or 'Not specified'}"
        )
        
        update_pipeline_record(pipeline_id, update_data, agent_name="hr_pipeline_agent")
        
        return {
            'success': True,
            'cancelled_event_id': event_id,
            'pipeline_id': pipeline_id
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel probe call: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def reschedule_probe_call(
    pipeline_id: str,
    new_start_time: str,
    new_end_time: str
) -> Dict[str, Any]:
    """
    Reschedule an existing probe call.
    
    Args:
        pipeline_id: Pipeline record ID
        new_start_time: New start time (ISO 8601)
        new_end_time: New end time (ISO 8601)
        
    Returns:
        Result dict
    """
    logger.info(f"Rescheduling probe call for pipeline {pipeline_id}")
    
    try:
        pipeline = get_pipeline_record(pipeline_id)
        if not pipeline:
            return {'success': False, 'error': 'Pipeline not found'}
        
        event_id = pipeline.probe_call_event_id
        if not event_id:
            # No existing event, just schedule a new one
            return schedule_probe_call(pipeline_id, new_start_time, new_end_time)
        
        # Update existing event
        from tools.calendar.events import update_event
        
        updates = {
            'start': {
                'dateTime': new_start_time,
                'timeZone': 'America/New_York'
            },
            'end': {
                'dateTime': new_end_time,
                'timeZone': 'America/New_York'
            }
        }
        
        update_success = update_event(event_id, updates)
        
        if not update_success:
            return {'success': False, 'error': 'Failed to update calendar event'}
        
        # Update pipeline
        update_data = PipelineUpdate(
            probe_call_datetime=datetime.fromisoformat(new_start_time.replace('Z', '+00:00'))
        )
        
        update_pipeline_record(pipeline_id, update_data, agent_name="hr_pipeline_agent")
        
        return {
            'success': True,
            'event_id': event_id,
            'new_start_time': new_start_time,
            'new_end_time': new_end_time,
            'pipeline_id': pipeline_id
        }
        
    except Exception as e:
        logger.error(f"Failed to reschedule probe call: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

