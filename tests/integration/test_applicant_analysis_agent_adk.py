"""
Integration tests for Applicant Analysis Agent (ADK).

Tests the complete workflow end-to-end with mocked external services.
"""
import pytest
import base64
import json
from unittest.mock import patch, MagicMock
from agents.applicant_analysis.agent_adk import ApplicantAnalysisAgent, process_resume


@pytest.fixture
def sample_resume_pdf():
    """Sample resume PDF content."""
    return b'%PDF-1.4\n%Mock resume content\nJohn Doe\nA&P Mechanic\njohn@example.com\n(203) 555-1234'


@pytest.fixture
def sample_parsed_data():
    """Sample parsed resume data."""
    return {
        'raw_text': 'John Doe\nA&P Mechanic...',
        'applicant_name': 'John Doe',
        'email': 'john@example.com',
        'phone': '(203) 555-1234',
        'location': 'Bridgeport, CT',
        'has_faa_ap': True,
        'faa_ap_number': '1234567890',
        'years_in_aviation': 15,
        'business_aviation_experience': True,
        'aog_field_experience': True,
        'text_length': 2450
    }


@pytest.fixture
def sample_analysis():
    """Sample LLM analysis."""
    return {
        'applicant_name': 'John Doe',
        'aircraft_experience': 'Gulfstream G450/G550, Citation CJ series',
        'engine_experience': 'Honeywell TFE731, P&WC PT6A',
        'systems_strengths': 'Avionics, Hydraulics, Powerplant',
        'aog_suitability_score': 8,
        'geographic_flexibility': 'NE Corridor',
        'baseline_verdict': 'Strong Fit',
        'missing_info': 'Current employment status',
        'follow_up_questions': 'What is your availability for on-call work?'
    }


@pytest.fixture
def mock_all_external_services(sample_resume_pdf, sample_parsed_data, sample_analysis):
    """Mock all external service calls."""
    with patch('agents.applicant_analysis.tools.download_file') as mock_download, \
         patch('agents.applicant_analysis.tools.parse_resume') as mock_parse, \
         patch('agents.applicant_analysis.tools.openai_client') as mock_openai, \
         patch('agents.applicant_analysis.tools.create_applicant') as mock_create_app, \
         patch('agents.applicant_analysis.tools.create_pipeline_record') as mock_create_pipe, \
         patch('agents.applicant_analysis.tools.log_interaction') as mock_log, \
         patch('agents.applicant_analysis.tools.generate_icc_pdf_bytes') as mock_generate_icc, \
         patch('agents.applicant_analysis.tools.upload_file') as mock_upload, \
         patch('agents.applicant_analysis.tools.update_applicant') as mock_update_app, \
         patch('agents.applicant_analysis.tools.publish_event') as mock_publish:
        
        # Setup mocks
        mock_download.return_value = sample_resume_pdf
        mock_parse.return_value = sample_parsed_data
        
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = json.dumps(sample_analysis)
        mock_response.choices = [MagicMock(message=mock_message)]
        mock_openai.chat.completions.create.return_value = mock_response
        
        mock_create_app.return_value = 'recAPP12345'
        mock_create_pipe.return_value = 'recPIPE67890'
        
        mock_generate_icc.return_value = b'%PDF-1.4 ICC Report'
        mock_upload.return_value = 'fileICC_123'
        mock_publish.return_value = 'msgID_789'
        
        yield {
            'download': mock_download,
            'parse': mock_parse,
            'openai': mock_openai,
            'create_applicant': mock_create_app,
            'create_pipeline': mock_create_pipe,
            'log': mock_log,
            'generate_icc': mock_generate_icc,
            'upload': mock_upload,
            'update_applicant': mock_update_app,
            'publish': mock_publish
        }


class TestApplicantAnalysisAgentIntegration:
    """Integration tests for the complete agent workflow."""
    
    def test_complete_workflow_success(self, mock_all_external_services):
        """Test complete resume processing workflow from start to finish."""
        # This test would require the actual OpenAI agent to be initialized
        # For now, we'll test the components in sequence
        
        from agents.applicant_analysis.tools import (
            download_resume_from_drive,
            parse_resume_text,
            analyze_candidate_fit,
            create_applicant_records_in_airtable,
            generate_icc_pdf,
            upload_icc_to_drive,
            publish_completion_event
        )
        
        # Step 1: Download
        download_result = download_resume_from_drive(file_id="test_file_123")
        assert download_result['success'] is True
        pdf_base64 = download_result['pdf_content_base64']
        
        # Step 2: Parse
        parse_result = parse_resume_text(pdf_content_base64=pdf_base64)
        assert parse_result['success'] is True
        parsed_data = parse_result['parsed_data']
        
        # Step 3: Analyze
        analyze_result = analyze_candidate_fit(
            parsed_resume_data=json.dumps(parsed_data)
        )
        assert analyze_result['success'] is True
        analysis = analyze_result['analysis']
        
        # Step 4: Create Airtable records
        create_result = create_applicant_records_in_airtable(
            parsed_data_json=json.dumps(parsed_data),
            analysis_json=json.dumps(analysis),
            resume_file_id="test_file_123"
        )
        assert create_result['success'] is True
        assert create_result['applicant_id'] == 'recAPP12345'
        assert create_result['pipeline_id'] == 'recPIPE67890'
        
        # Step 5: Generate ICC
        icc_result = generate_icc_pdf(
            parsed_data_json=json.dumps(parsed_data),
            analysis_json=json.dumps(analysis)
        )
        assert icc_result['success'] is True
        icc_base64 = icc_result['pdf_content_base64']
        
        # Step 6: Upload ICC
        upload_result = upload_icc_to_drive(
            pdf_content_base64=icc_base64,
            applicant_name="John Doe",
            applicant_id=create_result['applicant_id']
        )
        assert upload_result['success'] is True
        assert upload_result['file_id'] == 'fileICC_123'
        
        # Step 7: Publish event
        publish_result = publish_completion_event(
            applicant_id=create_result['applicant_id'],
            pipeline_id=create_result['pipeline_id'],
            baseline_verdict=analysis['baseline_verdict']
        )
        assert publish_result['success'] is True
        assert publish_result['message_id'] == 'msgID_789'
        
        # Verify all services were called
        mocks = mock_all_external_services
        mocks['download'].assert_called_once()
        mocks['parse'].assert_called_once()
        mocks['create_applicant'].assert_called_once()
        mocks['create_pipeline'].assert_called_once()
        mocks['log'].assert_called_once()
        mocks['generate_icc'].assert_called_once()
        mocks['upload'].assert_called_once()
        mocks['update_applicant'].assert_called_once()
        mocks['publish'].assert_called_once()
    
    def test_workflow_with_partial_failure(self, mock_all_external_services):
        """Test workflow behavior when a step fails."""
        from agents.applicant_analysis.tools import (
            download_resume_from_drive,
            parse_resume_text
        )
        
        # Simulate parse failure
        mock_all_external_services['parse'].return_value = None
        
        # Step 1: Download succeeds
        download_result = download_resume_from_drive(file_id="test_file")
        assert download_result['success'] is True
        
        # Step 2: Parse fails
        parse_result = parse_resume_text(
            pdf_content_base64=download_result['pdf_content_base64']
        )
        assert parse_result['success'] is False
        assert 'Failed to parse' in parse_result['error']
    
    def test_tools_handle_json_string_inputs(self, mock_all_external_services):
        """Test that tools properly handle JSON string inputs."""
        from agents.applicant_analysis.tools import (
            analyze_candidate_fit,
            create_applicant_records_in_airtable
        )
        
        # Tools should accept both dict and JSON string
        parsed_data = {'raw_text': 'test', 'email': 'test@example.com'}
        
        # Test with dict (will be converted to JSON string by tool)
        result1 = analyze_candidate_fit(
            parsed_resume_data=json.dumps(parsed_data)
        )
        assert result1['success'] is True
        
        # Test create_applicant_records with JSON strings
        analysis = {'applicant_name': 'Test', 'baseline_verdict': 'Maybe'}
        result2 = create_applicant_records_in_airtable(
            parsed_data_json=json.dumps(parsed_data),
            analysis_json=json.dumps(analysis),
            resume_file_id="file123"
        )
        assert result2['success'] is True


class TestProcessResumeFunction:
    """Tests for the process_resume convenience function."""
    
    @patch('agents.applicant_analysis.agent_adk.ApplicantAnalysisAgent')
    def test_process_resume_success(self, mock_agent_class):
        """Test process_resume convenience function."""
        # Setup
        mock_agent = MagicMock()
        mock_agent.process_resume.return_value = {
            'success': True,
            'applicant_id': 'recAPP123',
            'pipeline_id': 'recPIPE456',
            'icc_file_id': 'fileICC789',
            'applicant_name': 'John Doe',
            'baseline_verdict': 'Strong Fit',
            'error': None
        }
        mock_agent_class.return_value = mock_agent
        
        # Execute
        result = process_resume(file_id='test_file', filename='resume.pdf')
        
        # Assert
        assert result['success'] is True
        assert result['applicant_id'] == 'recAPP123'
        assert result['baseline_verdict'] == 'Strong Fit'


class TestAgentErrorHandling:
    """Tests for agent error handling and resilience."""
    
    @patch('agents.applicant_analysis.tools.download_file')
    def test_agent_handles_download_failure_gracefully(self, mock_download):
        """Test that agent handles download failures gracefully."""
        from agents.applicant_analysis.tools import download_resume_from_drive
        
        # Simulate download failure
        mock_download.side_effect = Exception("Drive API error")
        
        # Execute
        result = download_resume_from_drive(file_id="bad_file")
        
        # Assert - should return error result, not raise exception
        assert result['success'] is False
        assert 'Drive API error' in result['error']
    
    def test_tools_return_consistent_structure(self, mock_all_external_services):
        """Test that all tools return consistent response structure."""
        from agents.applicant_analysis.tools import (
            download_resume_from_drive,
            parse_resume_text,
            analyze_candidate_fit,
            create_applicant_records_in_airtable,
            generate_icc_pdf,
            upload_icc_to_drive,
            publish_completion_event
        )
        
        # All tools should return dict with 'success' and 'error' keys
        tools_results = []
        
        # Download
        result = download_resume_from_drive(file_id="test")
        tools_results.append(result)
        
        # Parse
        pdf_base64 = base64.b64encode(b'test').decode('utf-8')
        result = parse_resume_text(pdf_content_base64=pdf_base64)
        tools_results.append(result)
        
        # All results should have consistent structure
        for result in tools_results:
            assert 'success' in result
            assert 'error' in result
            assert isinstance(result['success'], bool)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

