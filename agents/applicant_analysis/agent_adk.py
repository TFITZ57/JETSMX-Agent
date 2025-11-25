"""
Google ADK Applicant Analysis Agent - Main entry point.

This agent uses pure Vertex AI with Gemini and Function Calling to process resumes.
"""
import json
from typing import Dict, Any, Optional, List, Callable
import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    Tool,
    FunctionDeclaration,
    Part,
    Content
)

from agents.applicant_analysis.tools import (
    download_resume_from_drive,
    parse_resume_text,
    analyze_candidate_fit,
    create_applicant_records_in_airtable,
    generate_icc_pdf,
    upload_icc_to_drive,
    publish_completion_event
)
from shared.logging.logger import setup_logger
from shared.config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()

# Initialize Vertex AI
vertexai.init(project=settings.gcp_project_id, location=settings.vertex_ai_location)

# System instruction for the agent
SYSTEM_INSTRUCTION = """You are the Applicant Analysis Agent for JetsMX, an AOG (Aircraft On Ground) aviation maintenance company.

Your role is to process resumes for on-call A&P technician positions. You have access to tools for:
1. Downloading resumes from Google Drive
2. Parsing and extracting structured data
3. Analyzing candidate fit using company requirements
4. Creating applicant records in Airtable
5. Generating Initial Candidate Coverage (ICC) reports
6. Publishing completion events

WORKFLOW STEPS:
For each resume, you MUST execute these steps in order:

1. Download the resume PDF from Google Drive using the file_id
2. Parse the PDF to extract text, contact info, A&P license details, and experience
3. Analyze the candidate's fit for JetsMX AOG positions (assess A&P status, business aviation experience, AOG experience, aircraft/engine match)
4. Create Applicant and Applicant Pipeline records in Airtable
5. Generate an ICC (Initial Candidate Coverage) PDF report
6. Upload the ICC PDF to Drive and update the Applicant record
7. Publish a completion event to Pub/Sub

IMPORTANT GUIDELINES:
- Always execute ALL steps in the workflow sequentially
- Pass data between steps correctly (use JSON strings where required)
- If any step fails, document the error clearly but continue if possible
- Prioritize accuracy and completeness over speed
- If critical information is missing, document it in the analysis

KEY REQUIREMENTS FOR JETSMX CANDIDATES:
- FAA A&P license (required)
- Business aviation experience (strongly preferred)
- AOG/field service experience (highly valuable)
- Mobile/on-call availability
- Geographic flexibility within NE corridor
- Relevant aircraft type experience (Gulfstream, Citation, Hawker, Falcon, etc.)

When complete, provide a summary with:
- Applicant ID
- Pipeline ID  
- ICC File ID
- Applicant Name
- Baseline Verdict
"""


def create_tool_config() -> List[FunctionDeclaration]:
    """Create function declarations for Gemini function calling."""
    
    return [
        FunctionDeclaration(
            name="download_resume_from_drive",
            description="Download a resume PDF from Google Drive",
            parameters={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "The Google Drive file ID"
                    }
                },
                "required": ["file_id"]
            }
        ),
        FunctionDeclaration(
            name="parse_resume_text",
            description="Parse resume PDF and extract structured data including contact info, licensing, and experience",
            parameters={
                "type": "object",
                "properties": {
                    "pdf_content_base64": {
                        "type": "string",
                        "description": "Base64-encoded PDF content from download_resume_from_drive"
                    }
                },
                "required": ["pdf_content_base64"]
            }
        ),
        FunctionDeclaration(
            name="analyze_candidate_fit",
            description="Analyze candidate suitability for AOG technician positions using LLM",
            parameters={
                "type": "object",
                "properties": {
                    "parsed_resume_data": {
                        "type": "string",
                        "description": "JSON string of parsed resume data (use json.dumps() to convert dict from parse_resume_text)"
                    }
                },
                "required": ["parsed_resume_data"]
            }
        ),
        FunctionDeclaration(
            name="create_applicant_records_in_airtable",
            description="Create Applicants and Applicant Pipeline records in Airtable",
            parameters={
                "type": "object",
                "properties": {
                    "parsed_data_json": {
                        "type": "string",
                        "description": "JSON string of parsed resume data from parse_resume_text"
                    },
                    "analysis_json": {
                        "type": "string",
                        "description": "JSON string of LLM analysis results from analyze_candidate_fit"
                    },
                    "resume_file_id": {
                        "type": "string",
                        "description": "Original resume Drive file ID"
                    }
                },
                "required": ["parsed_data_json", "analysis_json", "resume_file_id"]
            }
        ),
        FunctionDeclaration(
            name="generate_icc_pdf",
            description="Generate Initial Candidate Coverage (ICC) PDF report",
            parameters={
                "type": "object",
                "properties": {
                    "parsed_data_json": {
                        "type": "string",
                        "description": "JSON string of parsed resume data"
                    },
                    "analysis_json": {
                        "type": "string",
                        "description": "JSON string of analysis results"
                    }
                },
                "required": ["parsed_data_json", "analysis_json"]
            }
        ),
        FunctionDeclaration(
            name="upload_icc_to_drive",
            description="Upload ICC PDF to Drive and update Applicant record with file reference",
            parameters={
                "type": "object",
                "properties": {
                    "pdf_content_base64": {
                        "type": "string",
                        "description": "Base64-encoded PDF content from generate_icc_pdf"
                    },
                    "applicant_name": {
                        "type": "string",
                        "description": "Applicant name for filename from analyze_candidate_fit"
                    },
                    "applicant_id": {
                        "type": "string",
                        "description": "Airtable record ID from create_applicant_records_in_airtable"
                    },
                    "parent_folder_id": {
                        "type": "string",
                        "description": "Optional Drive folder ID for storage"
                    }
                },
                "required": ["pdf_content_base64", "applicant_name", "applicant_id"]
            }
        ),
        FunctionDeclaration(
            name="publish_completion_event",
            description="Publish applicant_profile_created event to Pub/Sub for downstream workflows",
            parameters={
                "type": "object",
                "properties": {
                    "applicant_id": {
                        "type": "string",
                        "description": "Airtable applicant record ID"
                    },
                    "pipeline_id": {
                        "type": "string",
                        "description": "Pipeline record ID"
                    },
                    "baseline_verdict": {
                        "type": "string",
                        "description": "Assessment verdict from analyze_candidate_fit"
                    }
                },
                "required": ["applicant_id", "pipeline_id", "baseline_verdict"]
            }
        )
    ]


# Map function names to actual Python functions
TOOL_FUNCTIONS: Dict[str, Callable] = {
    "download_resume_from_drive": download_resume_from_drive,
    "parse_resume_text": parse_resume_text,
    "analyze_candidate_fit": analyze_candidate_fit,
    "create_applicant_records_in_airtable": create_applicant_records_in_airtable,
    "generate_icc_pdf": generate_icc_pdf,
    "upload_icc_to_drive": upload_icc_to_drive,
    "publish_completion_event": publish_completion_event
}


class ApplicantAnalysisAgent:
    """Google ADK-based Applicant Analysis Agent using pure Vertex AI."""
    
    def __init__(self):
        """Initialize the agent with its tools and configuration."""
        self.model = None
        self.tools = None
        logger.info("Applicant Analysis Agent (ADK) initialized")
    
    def _create_model(self):
        """Create the Gemini model with function calling tools."""
        if self.model is not None:
            return self.model
        
        try:
            # Create tool config
            function_declarations = create_tool_config()
            tools = Tool(function_declarations=function_declarations)
            
            # Create model with tools
            model = GenerativeModel(
                "gemini-1.5-pro",
                tools=[tools],
                system_instruction=SYSTEM_INSTRUCTION
            )
            
            self.model = model
            self.tools = tools
            logger.info("Gemini model created successfully with function calling")
            return model
            
        except Exception as e:
            logger.error(f"Failed to create model: {str(e)}")
            raise
    
    def process_resume(self, file_id: str, filename: str) -> Dict[str, Any]:
        """
        Entry point for resume processing workflow.
        
        This method invokes the agent with a structured prompt that guides it
        through the complete workflow using the available tools.
        
        Args:
            file_id: Google Drive file ID of the resume PDF
            filename: Original filename for logging/reference
            
        Returns:
            ApplicantAnalysisResult dictionary with:
                - success (bool)
                - applicant_id (str)
                - pipeline_id (str)
                - icc_file_id (str)
                - applicant_name (str)
                - baseline_verdict (str)
                - error (Optional[str])
        """
        logger.info(f"Processing resume: {filename} ({file_id})")
        
        try:
            # Create or get model
            model = self._create_model()
            
            # Build detailed prompt
            prompt = f"""Process the following resume through the complete JetsMX applicant analysis workflow:

RESUME DETAILS:
- Drive File ID: {file_id}
- Filename: {filename}

INSTRUCTIONS:
Execute the workflow by calling the appropriate functions in sequence. Start by downloading the resume from Drive.

After completing all steps, provide a summary in JSON format with:
- success: true/false
- applicant_id: the Airtable record ID
- pipeline_id: the pipeline record ID
- icc_file_id: the ICC Drive file ID
- applicant_name: full name
- baseline_verdict: the assessment verdict
"""
            
            # Start chat session
            chat = model.start_chat()
            
            # Send initial prompt
            response = chat.send_message(prompt)
            
            # Handle function calling loop
            max_iterations = 15
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"Iteration {iteration}")
                
                # Check if model wants to call functions
                if not response.candidates[0].content.parts:
                    logger.warning("No parts in response")
                    break
                
                function_calls = []
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        function_calls.append(part.function_call)
                
                if not function_calls:
                    # No more function calls, we're done
                    logger.info("No more function calls, workflow complete")
                    break
                
                # Execute function calls
                function_responses = []
                for function_call in function_calls:
                    func_name = function_call.name
                    func_args = dict(function_call.args)
                    
                    logger.info(f"Calling function: {func_name}")
                    logger.debug(f"Arguments: {func_args}")
                    
                    # Execute the function
                    if func_name in TOOL_FUNCTIONS:
                        try:
                            result = TOOL_FUNCTIONS[func_name](**func_args)
                            logger.info(f"{func_name} result: {result.get('success', False)}")
                            
                            # Create function response
                            function_responses.append(
                                Part.from_function_response(
                                    name=func_name,
                                    response={"result": result}
                                )
                            )
                        except Exception as e:
                            logger.error(f"Function {func_name} failed: {str(e)}")
                            function_responses.append(
                                Part.from_function_response(
                                    name=func_name,
                                    response={"error": str(e), "success": False}
                                )
                            )
                    else:
                        logger.error(f"Unknown function: {func_name}")
                        function_responses.append(
                            Part.from_function_response(
                                name=func_name,
                                response={"error": f"Unknown function: {func_name}", "success": False}
                            )
                        )
                
                # Send function responses back to model
                response = chat.send_message(function_responses)
            
            # Extract final response
            final_text = response.text if hasattr(response, 'text') else str(response)
            logger.info(f"Final response: {final_text[:500]}...")
            
            # Parse response
            result = self._parse_agent_response(final_text)
            
            if result['success']:
                logger.info(f"Resume processing complete: {result.get('applicant_id')}")
            else:
                logger.error(f"Resume processing failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error processing resume: {str(e)}")
            return {
                'success': False,
                'applicant_id': None,
                'pipeline_id': None,
                'icc_file_id': None,
                'applicant_name': None,
                'baseline_verdict': None,
                'error': str(e)
            }
    
    def _parse_agent_response(self, result_text: str) -> Dict[str, Any]:
        """
        Parse the agent's response to extract structured result.
        
        Args:
            result_text: Text output from agent
            
        Returns:
            Structured result dictionary
        """
        # Try to extract JSON from the response
        try:
            # Look for JSON in the response
            if '{' in result_text and '}' in result_text:
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                json_text = result_text[json_start:json_end]
                parsed = json.loads(json_text)
                
                # Ensure all required fields are present
                if 'success' in parsed or 'applicant_id' in parsed:
                    return {
                        'success': parsed.get('success', True),
                        'applicant_id': parsed.get('applicant_id'),
                        'pipeline_id': parsed.get('pipeline_id'),
                        'icc_file_id': parsed.get('icc_file_id'),
                        'applicant_name': parsed.get('applicant_name'),
                        'baseline_verdict': parsed.get('baseline_verdict'),
                        'error': parsed.get('error')
                    }
        except json.JSONDecodeError:
            logger.warning("Could not parse JSON from agent response")
        
        # If we can't parse properly, return error
        return {
            'success': False,
            'applicant_id': None,
            'pipeline_id': None,
            'icc_file_id': None,
            'applicant_name': None,
            'baseline_verdict': None,
            'error': "Could not parse agent response"
        }


# Global agent instance
_agent_instance: Optional[ApplicantAnalysisAgent] = None


def get_applicant_analysis_agent() -> ApplicantAnalysisAgent:
    """Get or create the global agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ApplicantAnalysisAgent()
    return _agent_instance


def process_resume(file_id: str, filename: str) -> Dict[str, Any]:
    """
    Convenience function to process a resume using the global agent instance.
    
    Args:
        file_id: Google Drive file ID
        filename: Original filename
        
    Returns:
        ApplicantAnalysisResult dictionary
    """
    agent = get_applicant_analysis_agent()
    return agent.process_resume(file_id, filename)
