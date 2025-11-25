"""
HR Pipeline Agent - Manages hiring workflow with approvals.
"""
from datetime import datetime
from typing import Dict, Any
from agents.hr_pipeline.prompts import build_outreach_email
from agents.hr_pipeline.parse_reply import parse_applicant_reply
from agents.hr_pipeline.schedule_probe import schedule_probe_call
from tools.airtable.pipeline import get_pipeline_record, update_pipeline_record
from tools.gmail.drafts import create_draft_message
from tools.chat.messages import post_card
from tools.chat.cards import build_approval_card, build_probe_scheduling_card
from shared.models.pipeline import PipelineUpdate
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


class HRPipelineAgent:
    """Agent for HR pipeline workflows."""
    
    def __init__(self):
        """Initialize the agent."""
        self.settings = get_settings()
        logger.info("HR Pipeline Agent initialized")
    
    def generate_outreach_draft(self, pipeline_id: str) -> dict:
        """
        Generate outreach email draft for an applicant.
        
        Args:
            pipeline_id: Pipeline record ID
            
        Returns:
            Result with draft_id
        """
        try:
            logger.info(f"Generating outreach draft for pipeline {pipeline_id}")
            
            # Get pipeline record
            pipeline = get_pipeline_record(pipeline_id)
            if not pipeline:
                return {'success': False, 'error': 'Pipeline not found'}
            
            # Build email
            email_content = build_outreach_email(
                applicant_name=pipeline.applicant_name or "there",
                aircraft_types="business aviation"
            )
            
            # Create draft
            draft_result = create_draft_message(
                to=pipeline.primary_email,
                subject=email_content['subject'],
                body=email_content['body']
            )
            
            # Update pipeline
            from shared.models.pipeline import PipelineUpdate
            update_pipeline_record(
                pipeline_id,
                PipelineUpdate(
                    outreach_email_draft_id=draft_result['draft_id'],
                    email_draft_generated=True,
                    pipeline_stage="Outreach Draft Created"
                )
            )
            
            # Post Chat card for approval
            if self.settings.google_chat_space_id:
                card = build_approval_card(
                    title=f"Outreach Draft Ready: {pipeline.applicant_name}",
                    preview_text=email_content['body'][:500],
                    approve_action={
                        'actionMethodName': 'approve_outreach',
                        'parameters': [
                            {'key': 'pipeline_id', 'value': pipeline_id},
                            {'key': 'draft_id', 'value': draft_result['draft_id']}
                        ]
                    }
                )
                
                post_card(self.settings.google_chat_space_id, card)
            
            return {
                'success': True,
                'draft_id': draft_result['draft_id'],
                'pipeline_id': pipeline_id
            }
            
        except Exception as e:
            logger.error(f"Failed to generate outreach: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def parse_applicant_email_reply(
        self,
        thread_id: str,
        message_id: str,
        body_text: str,
        pipeline_id: str
    ) -> Dict[str, Any]:
        """
        Parse applicant email reply and propose probe call times.
        
        Args:
            thread_id: Gmail thread ID
            message_id: Gmail message ID
            body_text: Email body text
            pipeline_id: Pipeline record ID
            
        Returns:
            Result with parsed info and proposed times
        """
        try:
            logger.info(f"Parsing applicant reply for pipeline {pipeline_id}")
            
            # Get pipeline record
            pipeline = get_pipeline_record(pipeline_id)
            if not pipeline:
                return {'success': False, 'error': 'Pipeline not found'}
            
            # Parse the reply
            parsed = parse_applicant_reply(body_text)
            
            phone = parsed.get('phone')
            availability_windows = parsed.get('availability_windows', [])
            constraints = parsed.get('constraints')
            proposed_times = parsed.get('proposed_times', [])
            
            # Update pipeline with parsed info
            update_data = PipelineUpdate(
                last_reply_received_at=datetime.utcnow(),
                last_reply_summary=parsed.get('raw_summary'),
                confirmed_phone_number=phone,
                preferred_call_window_1=availability_windows[0] if len(availability_windows) > 0 else None,
                preferred_call_window_2=availability_windows[1] if len(availability_windows) > 1 else None,
                constraints=constraints,
                pipeline_stage="Applicant Responded"
            )
            
            update_pipeline_record(
                pipeline_id,
                update_data,
                agent_name="hr_pipeline_agent"
            )
            
            # Post Chat card with proposed times
            if self.settings.google_chat_space_id and proposed_times:
                card = build_probe_scheduling_card(
                    applicant_name=pipeline.applicant_name or "Applicant",
                    email_summary=f"Phone: {phone or 'Not provided'}\nAvailability: {', '.join(availability_windows) if availability_windows else 'See email'}",
                    proposed_times=proposed_times,
                    pipeline_id=pipeline_id
                )
                
                post_card(self.settings.google_chat_space_id, card)
                logger.info(f"Posted scheduling card to Chat for {pipeline.applicant_name}")
            
            return {
                'success': True,
                'pipeline_id': pipeline_id,
                'phone': phone,
                'availability_windows': availability_windows,
                'proposed_times': proposed_times,
                'constraints': constraints
            }
            
        except Exception as e:
            logger.error(f"Failed to parse applicant reply: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def approve_probe_schedule(
        self,
        pipeline_id: str,
        selected_time: Dict[str, str],
        phone_number: str = None
    ) -> Dict[str, Any]:
        """
        Approve and schedule a probe call (simulated approval for now).
        
        This would normally be triggered by a Chat card button click,
        but for MVP we can call it directly.
        
        Args:
            pipeline_id: Pipeline record ID
            selected_time: Dict with start_time and end_time (ISO 8601)
            phone_number: Confirmed phone number (optional)
            
        Returns:
            Result with event details
        """
        try:
            logger.info(f"Approving probe schedule for pipeline {pipeline_id}")
            
            start_time = selected_time.get('start_time')
            end_time = selected_time.get('end_time')
            
            if not start_time or not end_time:
                return {
                    'success': False,
                    'error': 'start_time and end_time required'
                }
            
            # Schedule the probe call
            result = schedule_probe_call(
                pipeline_id=pipeline_id,
                start_time=start_time,
                end_time=end_time,
                phone_number=phone_number
            )
            
            if result.get('success'):
                # Post confirmation to Chat
                if self.settings.google_chat_space_id:
                    from tools.chat.cards import build_notification_card
                    
                    card = build_notification_card(
                        title=f"Probe Call Scheduled: {result.get('applicant_name')}",
                        message=f"Event created successfully",
                        fields=[
                            {'label': 'Time', 'value': result.get('start_time')},
                            {'label': 'Meet Link', 'value': result.get('meet_link', 'N/A')}
                        ]
                    )
                    
                    post_card(self.settings.google_chat_space_id, card)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to approve probe schedule: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}


# Global instance
_hr_agent = None


def get_hr_pipeline_agent() -> HRPipelineAgent:
    """Get or create the global HR Pipeline agent instance."""
    global _hr_agent
    if _hr_agent is None:
        _hr_agent = HRPipelineAgent()
    return _hr_agent

