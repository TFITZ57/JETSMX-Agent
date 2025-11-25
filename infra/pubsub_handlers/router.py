"""
Event router that processes Pub/Sub messages and invokes agent workflows.
"""
import yaml
from typing import Dict, Any
from pathlib import Path
# Commented out until agents are ready
# from agents.applicant_analysis.agent_adk import get_applicant_analysis_agent
# from agents.hr_pipeline.agent import get_hr_pipeline_agent
from infra.pubsub_handlers.handlers.drive_handler import handle_drive_event
from infra.pubsub_handlers.handlers.gmail_handler import handle_gmail_event
from tools.airtable.pipeline import find_pipeline_by_thread_id
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


def load_routing_rules() -> Dict[str, Any]:
    """Load routing rules from event_routing.yaml."""
    schema_path = Path(__file__).parent.parent.parent / "SCHEMA" / "event_routing.yaml"
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def route_airtable_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route Airtable webhook events to appropriate agents.
    
    Args:
        event_data: Airtable webhook payload
        
    Returns:
        Processing result
    """
    table_id = event_data.get('table_id')
    record_id = event_data.get('record_id')
    changed_fields = event_data.get('changed_fields', [])
    new_values = event_data.get('new_values', {})
    
    logger.info(f"Routing Airtable event: table={table_id}, record={record_id}")
    
    # Route based on table and field changes
    if table_id == "applicant_pipeline":
        # Check for screening approval
        if "Screening Decision" in changed_fields:
            if new_values.get("screening_decision") == "Approve":
                if not new_values.get("email_draft_generated"):
                    logger.info("Triggering outreach draft generation")
                    # TODO: Implement when HR pipeline agent is ready
                    # hr_agent = get_hr_pipeline_agent()
                    # return hr_agent.generate_outreach_draft(record_id)
                    return {"status": "pending", "reason": "HR agent not yet implemented"}
        
        # Check for interview completion
        if "Pipeline Stage" in changed_fields:
            if new_values.get("pipeline_stage") == "Interview Complete":
                logger.info("Interview complete, notifying HR for decision")
                # Could trigger notification to Chat
                return {"status": "notification_sent"}
    
    return {"status": "no_action", "reason": "No matching routing rule"}


def route_gmail_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route Gmail notification events to the gmail_handler.
    
    Args:
        event_data: Gmail push notification data with history_id, or direct message data
        
    Returns:
        Processing result
    """
    history_id = event_data.get('history_id')
    message_id = event_data.get('message_id')
    thread_id = event_data.get('thread_id')
    
    logger.info(f"Routing Gmail event: history_id={history_id}, message_id={message_id}")
    
    try:
        # Use the dedicated gmail handler to process the event
        result = handle_gmail_event(event_data)
        return result
        
    except Exception as e:
        logger.error(f"Error routing Gmail event: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "history_id": history_id,
            "message_id": message_id
        }


def route_drive_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route Drive file change events.
    
    Uses the drive_handler to process Drive events, including resume uploads
    that trigger the Applicant Analysis Agent (ADK).
    
    Args:
        event_data: Drive notification data with file_id, name, mime_type, parents
        
    Returns:
        Processing result from handler
    """
    file_id = event_data.get('file_id')
    filename = event_data.get('name', 'unknown')
    resource_state = event_data.get('resource_state', 'unknown')
    
    logger.info(f"Routing Drive event: {filename} ({file_id}), state={resource_state}")
    
    try:
        # Use the dedicated drive handler which will route to appropriate workflows
        result = handle_drive_event(event_data)
        return result
        
    except Exception as e:
        logger.error(f"Error processing Drive event: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "file_id": file_id,
            "filename": filename
        }


def route_chat_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route Chat command/interaction events.
    
    Args:
        event_data: Chat command data
        
    Returns:
        Processing result
    """
    command = event_data.get('command', '')
    action_name = event_data.get('action_name', '')
    
    logger.info(f"Routing Chat event: command={command}, action={action_name}")
    
    # Route slash commands
    if command == '/probe':
        # Schedule probe call
        args = event_data.get('args', '')
        # hr_agent.schedule_probe_call(args)
        return {"status": "scheduled_probe"}
    
    # Route card interactions
    if action_name == 'approve_outreach':
        parameters = event_data.get('parameters', {})
        draft_id = parameters.get('draft_id')
        # Send the draft
        from tools.gmail.drafts import send_draft
        send_draft(draft_id)
        return {"status": "email_sent", "draft_id": draft_id}
    
    return {"status": "processed"}


def route_event(event_name: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main event router.
    
    Args:
        event_name: Name of the event (airtable, gmail, drive, chat)
        event_data: Event payload
        
    Returns:
        Processing result
    """
    logger.info(f"Routing event: {event_name}")
    
    try:
        if event_name == "airtable" or "airtable" in event_name:
            return route_airtable_event(event_data)
        elif event_name == "gmail" or "gmail" in event_name:
            return route_gmail_event(event_data)
        elif event_name == "drive" or "drive" in event_name:
            return route_drive_event(event_data)
        elif event_name == "chat" or "chat" in event_name:
            return route_chat_event(event_data)
        else:
            logger.warning(f"Unknown event type: {event_name}")
            return {"status": "unknown_event"}
            
    except Exception as e:
        logger.error(f"Error routing event: {str(e)}", exc_info=True)
        return {"status": "error", "error": str(e)}

