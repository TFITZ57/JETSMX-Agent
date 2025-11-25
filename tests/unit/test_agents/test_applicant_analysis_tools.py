"""
Unit tests for Applicant Analysis Agent ADK tools.

Tests each tool function independently with mocked dependencies.
"""
import pytest
import base64
import json
from unittest.mock import patch, MagicMock
from agents.applicant_analysis.tools import (
    download_resume_from_drive,
    parse_resume_text,
    analyze_candidate_fit,
    create_applicant_records_in_airtable,
    generate_icc_pdf,
    upload_icc_to_drive,
    publish_completion_event
)


class TestDownloadResumeFromDrive:
    """Tests for download_resume_from_drive tool."""
    
    @patch('agents.applicant_analysis.tools.download_file')
    def test_successful_download(self, mock_download):
        """Test successful resume download."""
        # Setup
        mock_content = b'%PDF-1.4 fake pdf content'
        mock_download.return_value = mock_content
        
        # Execute
        result = download_resume_from_drive.invoke({"file_id": "test_file_123"})
        
        # Assert
        assert result['success'] is True
        assert result['pdf_content_base64'] is not None
        assert result['file_size_bytes'] == len(mock_content)
        assert result['error'] is None
        
        # Verify content is properly encoded
        decoded = base64.b64decode(result['pdf_content_base64'])
        assert decoded == mock_content
    
    @patch('agents.applicant_analysis.tools.download_file')
    def test_download_failure(self, mock_download):
        """Test download failure handling."""
        # Setup
        mock_download.return_value = None
        
        # Execute
        result = download_resume_from_drive.invoke({"file_id": "bad_file"})
        
        # Assert
        assert result['success'] is False
        assert result['error'] is not None
        assert 'Failed to download' in result['error']
    
    @patch('agents.applicant_analysis.tools.download_file')
    def test_download_exception(self, mock_download):
        """Test exception handling during download."""
        # Setup
        mock_download.side_effect = Exception("Network error")
        
        # Execute
        result = download_resume_from_drive.invoke({"file_id": "test_file"})
        
        # Assert
        assert result['success'] is False
        assert 'Network error' in result['error']


class TestParseResumeText:
    """Tests for parse_resume_text tool."""
    
    @patch('agents.applicant_analysis.tools.parse_resume')
    def test_successful_parse(self, mock_parse):
        """Test successful resume parsing."""
        # Setup
        mock_parsed_data = {
            'raw_text': 'John Doe\nA&P Mechanic\n...',
            'email': 'john@example.com',
            'phone': '(203) 555-1234',
            'has_faa_ap': True,
            'faa_ap_number': '1234567890'
        }
        mock_parse.return_value = mock_parsed_data
        
        pdf_content = b'fake pdf'
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        # Execute
        result = parse_resume_text.invoke({"pdf_content_base64": pdf_base64})
        
        # Assert
        assert result['success'] is True
        assert result['parsed_data'] == mock_parsed_data
        assert result['error'] is None
    
    @patch('agents.applicant_analysis.tools.parse_resume')
    def test_parse_failure(self, mock_parse):
        """Test parse failure handling."""
        # Setup
        mock_parse.return_value = None
        
        pdf_base64 = base64.b64encode(b'fake pdf').decode('utf-8')
        
        # Execute
        result = parse_resume_text.invoke({"pdf_content_base64": pdf_base64})
        
        # Assert
        assert result['success'] is False
        assert 'Failed to parse' in result['error']


class TestAnalyzeCandidateFit:
    """Tests for analyze_candidate_fit tool."""
    
    @patch('agents.applicant_analysis.tools.ChatVertexAI')
    def test_successful_analysis(self, mock_llm_class):
        """Test successful candidate analysis."""
        # Setup
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        
        analysis_result = {
            'applicant_name': 'John Doe',
            'baseline_verdict': 'Strong Fit',
            'aog_suitability_score': 8,
            'aircraft_experience': 'Gulfstream G450/G550',
            'missing_info': 'None',
            'follow_up_questions': 'What is your availability?'
        }
        
        mock_response = MagicMock()
        mock_response.content = json.dumps(analysis_result)
        mock_llm.invoke.return_value = mock_response
        
        parsed_data = {
            'raw_text': 'Resume text...',
            'email': 'john@example.com',
            'has_faa_ap': True
        }
        
        # Execute
        result = analyze_candidate_fit.invoke({
            "parsed_resume_data": json.dumps(parsed_data)
        })
        
        # Assert
        assert result['success'] is True
        assert result['analysis']['applicant_name'] == 'John Doe'
        assert result['analysis']['baseline_verdict'] == 'Strong Fit'
        assert result['error'] is None
    
    @patch('agents.applicant_analysis.tools.ChatVertexAI')
    def test_analysis_with_json_markdown(self, mock_llm_class):
        """Test analysis with JSON in markdown code blocks."""
        # Setup
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        
        analysis_result = {'applicant_name': 'Jane Smith', 'baseline_verdict': 'Maybe'}
        
        mock_response = MagicMock()
        mock_response.content = f"```json\n{json.dumps(analysis_result)}\n```"
        mock_llm.invoke.return_value = mock_response
        
        parsed_data = {'raw_text': 'Resume...'}
        
        # Execute
        result = analyze_candidate_fit.invoke({
            "parsed_resume_data": json.dumps(parsed_data)
        })
        
        # Assert
        assert result['success'] is True
        assert result['analysis']['applicant_name'] == 'Jane Smith'


class TestCreateApplicantRecordsInAirtable:
    """Tests for create_applicant_records_in_airtable tool."""
    
    @patch('agents.applicant_analysis.tools.log_interaction')
    @patch('agents.applicant_analysis.tools.create_pipeline_record')
    @patch('agents.applicant_analysis.tools.create_applicant')
    def test_successful_record_creation(self, mock_create_applicant, mock_create_pipeline, mock_log):
        """Test successful Airtable record creation."""
        # Setup
        mock_create_applicant.return_value = 'recAPP123'
        mock_create_pipeline.return_value = 'recPIPE456'
        
        parsed_data = {
            'email': 'john@example.com',
            'phone': '(203) 555-1234',
            'has_faa_ap': True
        }
        
        analysis = {
            'applicant_name': 'John Doe',
            'baseline_verdict': 'Strong Fit',
            'aog_suitability_score': 8
        }
        
        # Execute
        result = create_applicant_records_in_airtable.invoke({
            "parsed_data_json": json.dumps(parsed_data),
            "analysis_json": json.dumps(analysis),
            "resume_file_id": "file123"
        })
        
        # Assert
        assert result['success'] is True
        assert result['applicant_id'] == 'recAPP123'
        assert result['pipeline_id'] == 'recPIPE456'
        assert result['error'] is None
        
        # Verify calls
        mock_create_applicant.assert_called_once()
        mock_create_pipeline.assert_called_once()
        mock_log.assert_called_once()


class TestGenerateICCPDF:
    """Tests for generate_icc_pdf tool."""
    
    @patch('agents.applicant_analysis.tools.generate_icc_pdf_bytes')
    def test_successful_icc_generation(self, mock_generate):
        """Test successful ICC PDF generation."""
        # Setup
        mock_pdf_bytes = b'%PDF-1.4 fake icc pdf'
        mock_generate.return_value = mock_pdf_bytes
        
        parsed_data = {'applicant_name': 'John Doe', 'email': 'john@example.com'}
        analysis = {'baseline_verdict': 'Strong Fit', 'aog_suitability_score': 8}
        
        # Execute
        result = generate_icc_pdf.invoke({
            "parsed_data_json": json.dumps(parsed_data),
            "analysis_json": json.dumps(analysis)
        })
        
        # Assert
        assert result['success'] is True
        assert result['pdf_content_base64'] is not None
        assert result['pdf_size_bytes'] == len(mock_pdf_bytes)
        assert result['error'] is None


class TestUploadICCToDrive:
    """Tests for upload_icc_to_drive tool."""
    
    @patch('agents.applicant_analysis.tools.update_applicant')
    @patch('agents.applicant_analysis.tools.upload_file')
    def test_successful_upload(self, mock_upload, mock_update):
        """Test successful ICC upload to Drive."""
        # Setup
        mock_upload.return_value = 'file_icc_123'
        
        pdf_bytes = b'fake pdf'
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Execute
        result = upload_icc_to_drive.invoke({
            "pdf_content_base64": pdf_base64,
            "applicant_name": "John Doe",
            "applicant_id": "recAPP123"
        })
        
        # Assert
        assert result['success'] is True
        assert result['file_id'] == 'file_icc_123'
        assert result['web_view_link'] is not None
        assert 'drive.google.com' in result['web_view_link']
        assert result['error'] is None
        
        # Verify calls
        mock_upload.assert_called_once()
        mock_update.assert_called_once()


class TestPublishCompletionEvent:
    """Tests for publish_completion_event tool."""
    
    @patch('agents.applicant_analysis.tools.publish_event')
    def test_successful_publish(self, mock_publish):
        """Test successful event publication."""
        # Setup
        mock_publish.return_value = 'msg_12345'
        
        # Execute
        result = publish_completion_event.invoke({
            "applicant_id": "recAPP123",
            "pipeline_id": "recPIPE456",
            "baseline_verdict": "Strong Fit"
        })
        
        # Assert
        assert result['success'] is True
        assert result['message_id'] == 'msg_12345'
        assert result['error'] is None
        
        # Verify event data structure
        call_args = mock_publish.call_args
        event_data = call_args[1]['event_data']
        assert event_data['event_type'] == 'applicant_profile_created'
        assert event_data['applicant_id'] == 'recAPP123'
        assert event_data['pipeline_id'] == 'recPIPE456'
        assert event_data['baseline_verdict'] == 'Strong Fit'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

