"""
Company Knowledge Base Agent - Read-only conversational agent using pure Vertex AI.
"""
import vertexai
from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration, Part
from typing import Dict, Any, Callable, List

from agents.company_kb.prompts import SYSTEM_PROMPT
from tools.airtable.tools import (
    airtable_get_applicant,
    airtable_get_pipeline,
    airtable_find_applicants
)
from tools.gmail.tools import gmail_get_message, gmail_get_thread, gmail_list_threads
from tools.calendar.tools import calendar_list_events
from tools.drive.tools import drive_get_file_metadata, drive_list_files_in_folder
from shared.logging.logger import setup_logger
from shared.config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()

# Initialize Vertex AI
vertexai.init(project=settings.google_cloud_project_id, location=settings.google_cloud_region or "us-central1")


# Map function names to actual Python functions
TOOL_FUNCTIONS: Dict[str, Callable] = {
    "airtable_get_applicant": airtable_get_applicant,
    "airtable_get_pipeline": airtable_get_pipeline,
    "airtable_find_applicants": airtable_find_applicants,
    "gmail_get_message": gmail_get_message,
    "gmail_get_thread": gmail_get_thread,
    "gmail_list_threads": gmail_list_threads,
    "calendar_list_events": calendar_list_events,
    "drive_get_file_metadata": drive_get_file_metadata,
    "drive_list_files_in_folder": drive_list_files_in_folder
}


def create_tool_config() -> List[FunctionDeclaration]:
    """Create function declarations for Gemini function calling."""
    
    return [
        FunctionDeclaration(
            name="airtable_get_applicant",
            description="Get an applicant by record ID from Airtable",
            parameters={
                "type": "object",
                "properties": {
                    "record_id": {"type": "string", "description": "Airtable record ID"}
                },
                "required": ["record_id"]
            }
        ),
        FunctionDeclaration(
            name="airtable_get_pipeline",
            description="Get a pipeline record by ID from Airtable",
            parameters={
                "type": "object",
                "properties": {
                    "record_id": {"type": "string", "description": "Airtable record ID"}
                },
                "required": ["record_id"]
            }
        ),
        FunctionDeclaration(
            name="airtable_find_applicants",
            description="Find applicants matching criteria in Airtable using formula",
            parameters={
                "type": "object",
                "properties": {
                    "formula": {
                        "type": "string",
                        "description": "Airtable formula (e.g., \"{Email} = 'test@example.com'\"). Leave empty to get all."
                    }
                },
                "required": []
            }
        ),
        FunctionDeclaration(
            name="gmail_get_message",
            description="Get a Gmail message by ID",
            parameters={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "Message ID"}
                },
                "required": ["message_id"]
            }
        ),
        FunctionDeclaration(
            name="gmail_get_thread",
            description="Get a Gmail thread by ID with all messages",
            parameters={
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string", "description": "Thread ID"}
                },
                "required": ["thread_id"]
            }
        ),
        FunctionDeclaration(
            name="gmail_list_threads",
            description="List Gmail threads matching a query",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gmail search query (e.g., 'from:user@example.com')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of threads to return (default 10)"
                    }
                },
                "required": []
            }
        ),
        FunctionDeclaration(
            name="calendar_list_events",
            description="List calendar events in a time range",
            parameters={
                "type": "object",
                "properties": {
                    "time_min": {
                        "type": "string",
                        "description": "Start time in ISO 8601 format (defaults to now)"
                    },
                    "time_max": {
                        "type": "string",
                        "description": "End time in ISO 8601 format"
                    }
                },
                "required": []
            }
        ),
        FunctionDeclaration(
            name="drive_get_file_metadata",
            description="Get Drive file metadata including name, MIME type, created time, web link",
            parameters={
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "Drive file ID"}
                },
                "required": ["file_id"]
            }
        ),
        FunctionDeclaration(
            name="drive_list_files_in_folder",
            description="List files in a Drive folder",
            parameters={
                "type": "object",
                "properties": {
                    "folder_id": {"type": "string", "description": "Folder ID"},
                    "mime_type": {
                        "type": "string",
                        "description": "Filter by MIME type (optional, e.g., 'application/pdf')"
                    }
                },
                "required": ["folder_id"]
            }
        )
    ]


class CompanyKBAgent:
    """Conversational agent for querying company data using pure Vertex AI."""
    
    def __init__(self):
        """Initialize the agent."""
        # Create tool config
        function_declarations = create_tool_config()
        tools = Tool(function_declarations=function_declarations)
        
        # Initialize model with tools
        self.model = GenerativeModel(
            "gemini-1.5-pro",
            tools=[tools],
            system_instruction=SYSTEM_PROMPT
        )
        
        logger.info("Company KB Agent initialized with pure Vertex AI")
    
    def query(self, question: str) -> str:
        """
        Answer a question using company data.
        
        Args:
            question: User's question
            
        Returns:
            Answer text
        """
        try:
            # Start chat session
            chat = self.model.start_chat()
            
            # Send initial question
            response = chat.send_message(question)
            
            # Handle function calling loop
            max_iterations = 10
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Check if model wants to call functions
                if not response.candidates[0].content.parts:
                    break
                
                function_calls = []
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        function_calls.append(part.function_call)
                
                if not function_calls:
                    # No more function calls, we're done
                    break
                
                # Execute function calls
                function_responses = []
                for function_call in function_calls:
                    func_name = function_call.name
                    func_args = dict(function_call.args)
                    
                    logger.info(f"Calling function: {func_name}")
                    
                    # Execute the function
                    if func_name in TOOL_FUNCTIONS:
                        try:
                            result = TOOL_FUNCTIONS[func_name](**func_args)
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
                                    response={"error": str(e)}
                                )
                            )
                    else:
                        logger.error(f"Unknown function: {func_name}")
                
                # Send function responses back to model
                response = chat.send_message(function_responses)
            
            # Return final text response
            return response.text if hasattr(response, 'text') else str(response)
            
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            return f"Error: {str(e)}"


# Global instance
_kb_agent = None


def get_company_kb_agent() -> CompanyKBAgent:
    """Get or create the global KB agent instance."""
    global _kb_agent
    if _kb_agent is None:
        _kb_agent = CompanyKBAgent()
    return _kb_agent
