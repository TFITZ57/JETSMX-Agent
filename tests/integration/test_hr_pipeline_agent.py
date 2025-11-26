"""
Integration tests for HR Pipeline Agent.

Tests the workflow for generating outreach, parsing replies, and scheduling.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from agents.hr_pipeline.agent import HRPipelineAgent, get_hr_pipeline_agent


@pytest.fixture
def mock_pipeline_record():
    """Sample pipeline record."""
    mock_pipeline = MagicMock()
    mock_pipeline.applicant_name = "Jane Smith"
    mock_pipeline.primary_email = "jane@example.com"
    mock_pipeline.pipeline_id = "recPIPE123"
    return mock_pipeline


@pytest.fixture
def mock_hr_dependencies():
    """Mock all external dependencies for HR agent."""
    with patch('agents.hr_pipeline.agent.get_pipeline_record') as mock_get_pipeline, \
         patch('agents.hr_pipeline.agent.update_pipeline_record') as mock_update, \
         patch('agents.hr_pipeline.agent.create_draft_message') as mock_draft, \
         patch('agents.hr_pipeline.agent.post_card') as mock_post_card, \
         patch('agents.hr_pipeline.agent.parse_applicant_reply') as mock_parse, \
         patch('agents.hr_pipeline.agent.schedule_probe_call') as mock_schedule:
        
        yield {
            'get_pipeline': mock_get_pipeline,
            'update_pipeline': mock_update,
            'create_draft': mock_draft,
            'post_card': mock_post_card,
            'parse_reply': mock_parse,
            'schedule_call': mock_schedule
        }


class TestHRPipelineAgent:
    """Integration tests for HR Pipeline Agent workflows."""
    
    def test_agent_initialization(self):
        """Test that agent initializes correctly."""
        agent = HRPipelineAgent()
        assert agent is not None
        assert agent.settings is not None
    
    def test_get_hr_pipeline_agent_singleton(self):
        """Test global singleton getter."""
        agent1 = get_hr_pipeline_agent()
        agent2 = get_hr_pipeline_agent()
        assert agent1 is agent2  # Should be same instance
    
    def test_generate_outreach_draft_success(self, mock_hr_dependencies, mock_pipeline_record):
        """Test successful outreach email draft generation."""
        # Setup
        mocks = mock_hr_dependencies
        mocks['get_pipeline'].return_value = mock_pipeline_record
        mocks['create_draft'].return_value = {
            'success': True,
            'draft_id': 'draft_abc123'
        }
        
        agent = HRPipelineAgent()
        
        # Execute
        result = agent.generate_outreach_draft(pipeline_id="recPIPE123")
        
        # Assert
        assert result['success'] is True
        assert result['draft_id'] == 'draft_abc123'
        assert result['pipeline_id'] == "recPIPE123"
        
        # Verify calls
        mocks['get_pipeline'].assert_called_once_with("recPIPE123")
        mocks['create_draft'].assert_called_once()
        mocks['update_pipeline'].assert_called_once()
    
    def test_generate_outreach_draft_pipeline_not_found(self, mock_hr_dependencies):
        """Test outreach generation with missing pipeline."""
        # Setup
        mocks = mock_hr_dependencies
        mocks['get_pipeline'].return_value = None
        
        agent = HRPipelineAgent()
        
        # Execute
        result = agent.generate_outreach_draft(pipeline_id="recINVALID")
        
        # Assert
        assert result['success'] is False
        assert 'Pipeline not found' in result['error']
        mocks['create_draft'].assert_not_called()
    
    def test_parse_applicant_email_reply_success(self, mock_hr_dependencies, mock_pipeline_record):
        """Test parsing applicant email reply."""
        # Setup
        mocks = mock_hr_dependencies
        mocks['get_pipeline'].return_value = mock_pipeline_record
        mocks['parse_reply'].return_value = {
            'phone': '(203) 555-9999',
            'availability_windows': ['Mon-Fri 9am-5pm EST', 'Weekends 10am-2pm'],
            'constraints': 'No calls during lunch 12-1pm',
            'proposed_times': [
                {
                    'start_time': '2025-11-27T10:00:00-05:00',
                    'end_time': '2025-11-27T10:30:00-05:00'
                }
            ],
            'raw_summary': 'Available weekdays, prefers morning calls'
        }
        
        agent = HRPipelineAgent()
        
        # Execute
        result = agent.parse_applicant_email_reply(
            thread_id="thread123",
            message_id="msg456",
            body_text="Hi, I'm available Mon-Fri 9-5. My phone is 203-555-9999.",
            pipeline_id="recPIPE123"
        )
        
        # Assert
        assert result['success'] is True
        assert result['phone'] == '(203) 555-9999'
        assert len(result['availability_windows']) == 2
        assert result['constraints'] == 'No calls during lunch 12-1pm'
        assert len(result['proposed_times']) == 1
        
        # Verify pipeline was updated
        mocks['update_pipeline'].assert_called_once()
        update_call_args = mocks['update_pipeline'].call_args
        assert update_call_args[0][0] == "recPIPE123"  # pipeline_id
    
    def test_parse_applicant_email_reply_pipeline_not_found(self, mock_hr_dependencies):
        """Test parsing reply with missing pipeline."""
        # Setup
        mocks = mock_hr_dependencies
        mocks['get_pipeline'].return_value = None
        
        agent = HRPipelineAgent()
        
        # Execute
        result = agent.parse_applicant_email_reply(
            thread_id="thread123",
            message_id="msg456",
            body_text="Some email text",
            pipeline_id="recINVALID"
        )
        
        # Assert
        assert result['success'] is False
        assert 'Pipeline not found' in result['error']
        mocks['parse_reply'].assert_not_called()
    
    def test_approve_probe_schedule_success(self, mock_hr_dependencies):
        """Test approving and scheduling a probe call."""
        # Setup
        mocks = mock_hr_dependencies
        
        start_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
        end_time = (datetime.utcnow() + timedelta(days=1, minutes=30)).isoformat()
        
        mocks['schedule_call'].return_value = {
            'success': True,
            'event_id': 'evt_789',
            'applicant_name': 'Jane Smith',
            'start_time': start_time,
            'meet_link': 'https://meet.google.com/abc-defg-hij'
        }
        
        agent = HRPipelineAgent()
        
        # Execute
        result = agent.approve_probe_schedule(
            pipeline_id="recPIPE123",
            selected_time={
                'start_time': start_time,
                'end_time': end_time
            },
            phone_number='(203) 555-9999'
        )
        
        # Assert
        assert result['success'] is True
        assert result['event_id'] == 'evt_789'
        assert 'meet_link' in result
        
        # Verify schedule was called
        mocks['schedule_call'].assert_called_once_with(
            pipeline_id="recPIPE123",
            start_time=start_time,
            end_time=end_time,
            phone_number='(203) 555-9999'
        )
    
    def test_approve_probe_schedule_missing_times(self, mock_hr_dependencies):
        """Test probe scheduling with missing time parameters."""
        agent = HRPipelineAgent()
        
        # Execute
        result = agent.approve_probe_schedule(
            pipeline_id="recPIPE123",
            selected_time={},  # Missing start_time and end_time
            phone_number='(203) 555-9999'
        )
        
        # Assert
        assert result['success'] is False
        assert 'start_time and end_time required' in result['error']
        mock_hr_dependencies['schedule_call'].assert_not_called()
    
    def test_error_handling_in_methods(self, mock_hr_dependencies):
        """Test that agent methods handle exceptions gracefully."""
        # Setup - simulate exception
        mocks = mock_hr_dependencies
        mocks['get_pipeline'].side_effect = Exception("Database connection error")
        
        agent = HRPipelineAgent()
        
        # Test outreach generation error handling
        result = agent.generate_outreach_draft(pipeline_id="recPIPE123")
        assert result['success'] is False
        assert 'Database connection error' in result['error']
        
        # Reset and test reply parsing error handling
        mocks['get_pipeline'].side_effect = Exception("Network timeout")
        
        result = agent.parse_applicant_email_reply(
            thread_id="thread123",
            message_id="msg456",
            body_text="Test",
            pipeline_id="recPIPE123"
        )
        assert result['success'] is False
        assert 'Network timeout' in result['error']


class TestHRPipelineWorkflowIntegration:
    """Test complete HR pipeline workflow scenarios."""
    
    def test_full_outreach_to_scheduling_workflow(self, mock_hr_dependencies, mock_pipeline_record):
        """Test complete workflow: outreach -> reply -> schedule."""
        mocks = mock_hr_dependencies
        mocks['get_pipeline'].return_value = mock_pipeline_record
        
        agent = HRPipelineAgent()
        
        # Step 1: Generate outreach draft
        mocks['create_draft'].return_value = {
            'success': True,
            'draft_id': 'draft_xyz'
        }
        
        result1 = agent.generate_outreach_draft(pipeline_id="recPIPE123")
        assert result1['success'] is True
        assert result1['draft_id'] == 'draft_xyz'
        
        # Step 2: Parse applicant reply
        mocks['parse_reply'].return_value = {
            'phone': '(203) 555-1111',
            'availability_windows': ['Mon-Fri 9-5'],
            'constraints': None,
            'proposed_times': [
                {
                    'start_time': '2025-11-27T14:00:00-05:00',
                    'end_time': '2025-11-27T14:30:00-05:00'
                }
            ],
            'raw_summary': 'Available weekdays'
        }
        
        result2 = agent.parse_applicant_email_reply(
            thread_id="thread_abc",
            message_id="msg_123",
            body_text="I'm available Mon-Fri 9-5. Call me at 203-555-1111.",
            pipeline_id="recPIPE123"
        )
        assert result2['success'] is True
        assert result2['phone'] == '(203) 555-1111'
        
        # Step 3: Schedule probe call
        mocks['schedule_call'].return_value = {
            'success': True,
            'event_id': 'evt_final',
            'applicant_name': 'Jane Smith',
            'start_time': '2025-11-27T14:00:00-05:00',
            'meet_link': 'https://meet.google.com/xyz'
        }
        
        result3 = agent.approve_probe_schedule(
            pipeline_id="recPIPE123",
            selected_time=result2['proposed_times'][0],
            phone_number=result2['phone']
        )
        assert result3['success'] is True
        assert result3['event_id'] == 'evt_final'
        
        # Verify all steps executed
        assert mocks['get_pipeline'].call_count >= 2
        mocks['create_draft'].assert_called_once()
        mocks['parse_reply'].assert_called_once()
        mocks['schedule_call'].assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])






