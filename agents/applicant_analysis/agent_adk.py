"""
OpenAI Applicant Analysis Agent - Main entry point.

This agent uses OpenAI with GPT-5.1 and Function Calling to process resumes.
"""
import json
from typing import Dict, Any, Optional, List, Callable
from openai import OpenAI

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

# Initialize OpenAI client
openai_client = OpenAI(api_key=settings.openai_api_key)

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


def create_tool_config() -> List[Dict[str, Any]]:
    """Create function declarations for OpenAI function calling."""
    
    return [
        {
            "type": "function",
            "function": {
                "name": "download_resume_from_drive",
                "description": "Download a resume PDF from Google Drive",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_id": {
                            "type": "string",
                            "description": "The Google Drive file ID"
                        }
                    },
                    "required": ["file_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "parse_resume_text",
                "description": "Parse resume PDF and extract structured data including contact info, licensing, and experience",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pdf_content_base64": {
                            "type": "string",
                            "description": "Base64-encoded PDF content from download_resume_from_drive"
                        }
                    },
                    "required": ["pdf_content_base64"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_candidate_fit",
                "description": "Analyze candidate suitability for AOG technician positions using LLM",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "parsed_resume_data": {
                            "type": "string",
                            "description": "JSON string of parsed resume data (use json.dumps() to convert dict from parse_resume_text)"
                        }
                    },
                    "required": ["parsed_resume_data"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_applicant_records_in_airtable",
                "description": "Create Applicants and Applicant Pipeline records in Airtable",
                "parameters": {
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
            }
        },
        {
            "type": "function",
            "function": {
                "name": "generate_icc_pdf",
                "description": "Generate Initial Candidate Coverage (ICC) PDF report",
                "parameters": {
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
            }
        },
        {
            "type": "function",
            "function": {
                "name": "upload_icc_to_drive",
                "description": "Upload ICC PDF to Drive and update Applicant record with file reference",
                "parameters": {
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
            }
        },
        {
            "type": "function",
            "function": {
                "name": "publish_completion_event",
                "description": "Publish applicant_profile_created event to Pub/Sub for downstream workflows",
                "parameters": {
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
            }
        }
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
    """OpenAI-based Applicant Analysis Agent using GPT-5.1."""
    
    def __init__(self):
        """Initialize the agent with its tools and configuration."""
        self.client = openai_client
        self.tools = create_tool_config()
        logger.info("Applicant Analysis Agent (OpenAI) initialized")
    
    def query(self, file_id: str, filename: str = "resume.pdf") -> Dict[str, Any]:
        """
        Query method for agent compatibility.
        
        This is the entry point when the agent is invoked.
        
        Args:
            file_id: Google Drive file ID of the resume PDF
            filename: Original filename (optional, defaults to "resume.pdf")
            
        Returns:
            ApplicantAnalysisResult dictionary
        """
        return self.process_resume(file_id=file_id, filename=filename)
    
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
            
            # Initialize messages
            messages = [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt}
            ]
            
            # Handle function calling loop
            max_iterations = 15
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"Iteration {iteration}")
                
                # Call OpenAI API
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo",  # Using GPT-4 Turbo (gpt-5.1 doesn't exist yet)
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto"
                )
                
                response_message = response.choices[0].message
                
                # Check if there are tool calls
                if not response_message.tool_calls:
                    # No more function calls, we're done
                    logger.info("No more function calls, workflow complete")
                    messages.append(response_message)
                    break
                
                # Add assistant message with tool calls
                messages.append(response_message)
                
                # Execute function calls
                for tool_call in response_message.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Calling function: {func_name}")
                    logger.debug(f"Arguments: {func_args}")
                    
                    # Execute the function
                    if func_name in TOOL_FUNCTIONS:
                        try:
                            result = TOOL_FUNCTIONS[func_name](**func_args)
                            logger.info(f"{func_name} result: {result.get('success', False)}")
                            
                            # Add function result to messages
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": func_name,
                                "content": json.dumps({"result": result})
                            })
                        except Exception as e:
                            logger.error(f"Function {func_name} failed: {str(e)}")
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": func_name,
                                "content": json.dumps({"error": str(e), "success": False})
                            })
                    else:
                        logger.error(f"Unknown function: {func_name}")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": json.dumps({"error": f"Unknown function: {func_name}", "success": False})
                        })
            
            # Extract final response
            final_text = response_message.content if response_message.content else ""
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
