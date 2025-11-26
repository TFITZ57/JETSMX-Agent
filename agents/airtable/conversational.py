"""
Conversational interface for natural language Airtable operations.
"""
import json
from typing import Dict, Any, Optional, List, Callable
from openai import OpenAI
from agents.airtable.prompts import (
    SYSTEM_PROMPT,
    QUERY_CLARIFICATION_PROMPT,
    ERROR_HANDLING_PROMPT,
    CONFIRMATION_PROMPT
)
from agents.airtable.query_engine import QueryEngine
from agents.airtable.bulk_operations import BulkOperationManager
from tools.airtable.export import export_to_csv, export_to_json, export_to_excel
from tools.airtable.analytics import Analytics, PipelineAnalytics, ApplicantAnalytics
from tools.airtable.schema import get_schema_manager
from tools.airtable_tools import create_record, update_record, get_record
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


class ConversationalAgent:
    """Natural language interface for Airtable operations."""
    
    def __init__(self):
        """Initialize conversational agent."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.query_engine = QueryEngine()
        self.bulk_ops = BulkOperationManager()
        self.schema = get_schema_manager()
        self.system_prompt = SYSTEM_PROMPT
        
        # Tool function mapping
        self.tools = self._create_tool_definitions()
        self.tool_functions = self._create_tool_functions()
        
        logger.info("Conversational Airtable Agent initialized")
    
    def _create_tool_definitions(self) -> List[Dict[str, Any]]:
        """Create OpenAI function definitions for tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_records",
                    "description": "Search for records in a table using filters",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table": {"type": "string", "description": "Table name"},
                            "search_term": {"type": "string", "description": "Text to search for (optional)"},
                            "filters": {
                                "type": "array",
                                "description": "List of filters (field, op, value)",
                                "items": {"type": "object"}
                            },
                            "max_records": {"type": "integer", "description": "Max records to return"}
                        },
                        "required": ["table"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_record_by_id",
                    "description": "Get a single record by its ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table": {"type": "string", "description": "Table name"},
                            "record_id": {"type": "string", "description": "Record ID"}
                        },
                        "required": ["table", "record_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_record",
                    "description": "Create a new record in a table",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table": {"type": "string", "description": "Table name"},
                            "fields": {"type": "object", "description": "Field values for the new record"}
                        },
                        "required": ["table", "fields"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_record",
                    "description": "Update an existing record",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table": {"type": "string", "description": "Table name"},
                            "record_id": {"type": "string", "description": "Record ID"},
                            "fields": {"type": "object", "description": "Fields to update"}
                        },
                        "required": ["table", "record_id", "fields"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "count_records",
                    "description": "Count records matching criteria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table": {"type": "string", "description": "Table name"},
                            "filters": {
                                "type": "array",
                                "description": "Optional filters",
                                "items": {"type": "object"}
                            }
                        },
                        "required": ["table"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "group_and_count",
                    "description": "Count records grouped by a field",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table": {"type": "string", "description": "Table name"},
                            "field": {"type": "string", "description": "Field to group by"}
                        },
                        "required": ["table", "field"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "export_data",
                    "description": "Export records to CSV, JSON, or Excel",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table": {"type": "string", "description": "Table name"},
                            "format": {"type": "string", "enum": ["csv", "json", "excel"]},
                            "filters": {
                                "type": "array",
                                "description": "Optional filters",
                                "items": {"type": "object"}
                            }
                        },
                        "required": ["table", "format"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_table_schema",
                    "description": "Get the schema/structure of a table",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "table": {"type": "string", "description": "Table name"}
                        },
                        "required": ["table"]
                    }
                }
            }
        ]
    
    def _create_tool_functions(self) -> Dict[str, Callable]:
        """Map tool names to actual functions."""
        return {
            "query_records": self._tool_query_records,
            "get_record_by_id": self._tool_get_record_by_id,
            "create_record": self._tool_create_record,
            "update_record": self._tool_update_record,
            "count_records": self._tool_count_records,
            "group_and_count": self._tool_group_and_count,
            "export_data": self._tool_export_data,
            "get_table_schema": self._tool_get_table_schema
        }
    
    def _tool_query_records(
        self,
        table: str,
        search_term: Optional[str] = None,
        filters: Optional[List[Dict]] = None,
        max_records: Optional[int] = 100
    ) -> Dict[str, Any]:
        """Tool: Query records."""
        try:
            if search_term:
                records = self.query_engine.search(table, search_term)
            elif filters:
                records = self.query_engine.filter_query(table, filters, max_records=max_records)
            else:
                records = self.query_engine.simple_query(table, max_records=max_records)
            
            return {
                "success": True,
                "count": len(records),
                "records": records[:max_records] if max_records else records
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_get_record_by_id(self, table: str, record_id: str) -> Dict[str, Any]:
        """Tool: Get record by ID."""
        try:
            record = self.query_engine.get_by_id(table, record_id)
            if record:
                return {"success": True, "record": record}
            return {"success": False, "error": "Record not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_create_record(self, table: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Create record."""
        try:
            record = create_record(
                settings.airtable_base_id,
                table,
                fields
            )
            return {"success": True, "record": record}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_update_record(
        self,
        table: str,
        record_id: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Tool: Update record."""
        try:
            record = update_record(
                settings.airtable_base_id,
                table,
                record_id,
                fields
            )
            return {"success": True, "record": record}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_count_records(
        self,
        table: str,
        filters: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Tool: Count records."""
        try:
            if filters:
                records = self.query_engine.filter_query(table, filters)
            else:
                records = self.query_engine.simple_query(table)
            
            return {"success": True, "count": len(records)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_group_and_count(self, table: str, field: str) -> Dict[str, Any]:
        """Tool: Group and count."""
        try:
            records = self.query_engine.simple_query(table)
            counts = Analytics.count_by_field(records, field)
            return {"success": True, "counts": counts}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_export_data(
        self,
        table: str,
        format: str,
        filters: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Tool: Export data."""
        try:
            if filters:
                records = self.query_engine.filter_query(table, filters)
            else:
                records = self.query_engine.simple_query(table)
            
            if format == "csv":
                data = export_to_csv(records)
            elif format == "json":
                data = export_to_json(records)
            elif format == "excel":
                data = export_to_excel(records)
                # For Excel, return base64 encoded
                import base64
                data = base64.b64encode(data).decode()
            else:
                return {"success": False, "error": f"Unknown format: {format}"}
            
            return {
                "success": True,
                "format": format,
                "record_count": len(records),
                "data": data
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _tool_get_table_schema(self, table: str) -> Dict[str, Any]:
        """Tool: Get table schema."""
        try:
            schema = self.schema.describe_table(table)
            if schema:
                return {"success": True, "schema": schema}
            return {"success": False, "error": "Table not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def query(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Process a natural language query.
        
        Args:
            user_message: User's natural language request
            conversation_history: Optional previous messages
            
        Returns:
            Response text
        """
        try:
            # Build messages
            messages = [{"role": "system", "content": self.system_prompt}]
            
            if conversation_history:
                messages.extend(conversation_history)
            
            messages.append({"role": "user", "content": user_message})
            
            # Function calling loop
            max_iterations = 10
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                response = self.client.chat.completions.create(
                    model=settings.openai_model or "gpt-4o",
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto"
                )
                
                response_message = response.choices[0].message
                
                # No more tool calls - done
                if not response_message.tool_calls:
                    messages.append(response_message)
                    break
                
                # Add assistant message with tool calls
                messages.append(response_message)
                
                # Execute tool calls
                for tool_call in response_message.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Executing tool: {func_name}")
                    
                    if func_name in self.tool_functions:
                        try:
                            result = self.tool_functions[func_name](**func_args)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": func_name,
                                "content": json.dumps(result)
                            })
                        except Exception as e:
                            logger.error(f"Tool {func_name} failed: {e}")
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": func_name,
                                "content": json.dumps({"success": False, "error": str(e)})
                            })
            
            # Return final response
            return response_message.content if response_message.content else "Operation completed"
            
        except Exception as e:
            logger.error(f"Conversational query failed: {e}")
            return f"I encountered an error: {str(e)}"

