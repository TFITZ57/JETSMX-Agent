"""
Pub/Sub handler for asynchronous Airtable commands.
"""
import json
import base64
from typing import Dict, Any
from datetime import datetime
import time
import requests
from agents.airtable.agent import get_airtable_agent
from shared.models.airtable_commands import (
    QueryCommand,
    BulkCreateCommand,
    BulkUpdateCommand,
    BulkDeleteCommand,
    ExportCommand,
    AnalyticsCommand,
    CommandResult
)
from tools.pubsub.publisher import publish_message
from shared.logging.logger import setup_logger
from shared.config.settings import get_settings

logger = setup_logger(__name__)
settings = get_settings()


class AirtableCommandHandler:
    """Handle asynchronous Airtable commands from Pub/Sub."""
    
    def __init__(self):
        """Initialize handler."""
        self.agent = get_airtable_agent()
    
    def handle_command(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route and execute a command.
        
        Args:
            message_data: Decoded Pub/Sub message data
            
        Returns:
            Command result
        """
        command_type = message_data.get("command_type")
        
        if command_type == "query":
            return self._handle_query(QueryCommand(**message_data))
        elif command_type == "bulk_create":
            return self._handle_bulk_create(BulkCreateCommand(**message_data))
        elif command_type == "bulk_update":
            return self._handle_bulk_update(BulkUpdateCommand(**message_data))
        elif command_type == "bulk_delete":
            return self._handle_bulk_delete(BulkDeleteCommand(**message_data))
        elif command_type == "export":
            return self._handle_export(ExportCommand(**message_data))
        elif command_type == "analytics":
            return self._handle_analytics(AnalyticsCommand(**message_data))
        else:
            return {
                "success": False,
                "error": f"Unknown command type: {command_type}"
            }
    
    def _handle_query(self, command: QueryCommand) -> Dict[str, Any]:
        """Handle query command."""
        start_time = time.time()
        
        try:
            records = self.agent.query(
                command.table,
                filters=command.filters,
                max_records=command.max_records
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            result = CommandResult(
                command_id=command.command_id,
                success=True,
                result={
                    "count": len(records),
                    "records": records
                },
                execution_time_ms=execution_time
            )
            
            logger.info(f"Query command {command.command_id} completed: {len(records)} records")
            return result.model_dump()
        except Exception as e:
            logger.error(f"Query command {command.command_id} failed: {e}")
            return CommandResult(
                command_id=command.command_id,
                success=False,
                error=str(e)
            ).model_dump()
    
    def _handle_bulk_create(self, command: BulkCreateCommand) -> Dict[str, Any]:
        """Handle bulk create command."""
        start_time = time.time()
        
        try:
            result = self.agent.bulk_create(
                command.table,
                command.records,
                batch_size=command.batch_size,
                validate=command.validate,
                initiated_by=command.initiated_by,
                reason=f"Pub/Sub command {command.command_id}"
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            command_result = CommandResult(
                command_id=command.command_id,
                success=result.success_count == result.total_count,
                result=result.to_dict(),
                execution_time_ms=execution_time
            )
            
            logger.info(
                f"Bulk create command {command.command_id} completed: "
                f"{result.success_count}/{result.total_count} successful"
            )
            return command_result.model_dump()
        except Exception as e:
            logger.error(f"Bulk create command {command.command_id} failed: {e}")
            return CommandResult(
                command_id=command.command_id,
                success=False,
                error=str(e)
            ).model_dump()
    
    def _handle_bulk_update(self, command: BulkUpdateCommand) -> Dict[str, Any]:
        """Handle bulk update command."""
        start_time = time.time()
        
        try:
            result = self.agent.bulk_update(
                command.table,
                command.updates,
                batch_size=command.batch_size,
                validate=command.validate,
                replace=command.replace,
                initiated_by=command.initiated_by,
                reason=f"Pub/Sub command {command.command_id}"
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            command_result = CommandResult(
                command_id=command.command_id,
                success=result.success_count == result.total_count,
                result=result.to_dict(),
                execution_time_ms=execution_time
            )
            
            logger.info(
                f"Bulk update command {command.command_id} completed: "
                f"{result.success_count}/{result.total_count} successful"
            )
            return command_result.model_dump()
        except Exception as e:
            logger.error(f"Bulk update command {command.command_id} failed: {e}")
            return CommandResult(
                command_id=command.command_id,
                success=False,
                error=str(e)
            ).model_dump()
    
    def _handle_bulk_delete(self, command: BulkDeleteCommand) -> Dict[str, Any]:
        """Handle bulk delete command."""
        start_time = time.time()
        
        try:
            result = self.agent.bulk_delete(
                command.table,
                command.record_ids,
                batch_size=command.batch_size,
                initiated_by=command.initiated_by,
                reason=f"Pub/Sub command {command.command_id}"
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            command_result = CommandResult(
                command_id=command.command_id,
                success=result.success_count == result.total_count,
                result=result.to_dict(),
                execution_time_ms=execution_time
            )
            
            logger.info(
                f"Bulk delete command {command.command_id} completed: "
                f"{result.success_count}/{result.total_count} successful"
            )
            return command_result.model_dump()
        except Exception as e:
            logger.error(f"Bulk delete command {command.command_id} failed: {e}")
            return CommandResult(
                command_id=command.command_id,
                success=False,
                error=str(e)
            ).model_dump()
    
    def _handle_export(self, command: ExportCommand) -> Dict[str, Any]:
        """Handle export command."""
        start_time = time.time()
        
        try:
            data = self.agent.export(
                command.table,
                command.format,
                filters=command.filters
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            # If upload_to is specified, upload to Cloud Storage
            if command.upload_to:
                from google.cloud import storage
                
                client = storage.Client()
                bucket_name, blob_path = command.upload_to.split("/", 1)
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_path)
                
                if command.format == "excel":
                    # Excel is already base64, decode it
                    blob.upload_from_string(base64.b64decode(data))
                else:
                    blob.upload_from_string(data)
                
                logger.info(f"Exported data uploaded to gs://{command.upload_to}")
                result_data = {"uploaded_to": f"gs://{command.upload_to}"}
            else:
                result_data = {"data": data}
            
            command_result = CommandResult(
                command_id=command.command_id,
                success=True,
                result=result_data,
                execution_time_ms=execution_time
            )
            
            logger.info(f"Export command {command.command_id} completed")
            return command_result.model_dump()
        except Exception as e:
            logger.error(f"Export command {command.command_id} failed: {e}")
            return CommandResult(
                command_id=command.command_id,
                success=False,
                error=str(e)
            ).model_dump()
    
    def _handle_analytics(self, command: AnalyticsCommand) -> Dict[str, Any]:
        """Handle analytics command."""
        start_time = time.time()
        
        try:
            result = self.agent.aggregate(
                command.table,
                command.agg_type,
                command.field,
                group_by=command.group_by,
                filters=command.filters
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            command_result = CommandResult(
                command_id=command.command_id,
                success=True,
                result=result,
                execution_time_ms=execution_time
            )
            
            logger.info(f"Analytics command {command.command_id} completed")
            return command_result.model_dump()
        except Exception as e:
            logger.error(f"Analytics command {command.command_id} failed: {e}")
            return CommandResult(
                command_id=command.command_id,
                success=False,
                error=str(e)
            ).model_dump()
    
    def publish_result(self, result: Dict[str, Any], callback_url: str = None, callback_topic: str = None):
        """Publish command result to callback destination."""
        if callback_url:
            try:
                response = requests.post(callback_url, json=result, timeout=30)
                response.raise_for_status()
                logger.info(f"Result posted to callback URL: {callback_url}")
            except Exception as e:
                logger.error(f"Failed to post result to {callback_url}: {e}")
        
        if callback_topic:
            try:
                publish_message(callback_topic, result)
                logger.info(f"Result published to topic: {callback_topic}")
            except Exception as e:
                logger.error(f"Failed to publish result to {callback_topic}: {e}")


# Create handler instance
handler = AirtableCommandHandler()


def handle_airtable_command(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Cloud Function entry point for Airtable commands.
    
    Args:
        event: Pub/Sub event
        context: Cloud Functions context
        
    Returns:
        Processing result
    """
    try:
        # Decode Pub/Sub message
        if "data" in event:
            message_data = base64.b64decode(event["data"]).decode("utf-8")
            message_dict = json.loads(message_data)
        else:
            message_dict = event
        
        logger.info(f"Processing command: {message_dict.get('command_type')}")
        
        # Execute command
        result = handler.handle_command(message_dict)
        
        # Publish result if callbacks specified
        callback_url = message_dict.get("callback_url")
        callback_topic = message_dict.get("callback_topic")
        
        if callback_url or callback_topic:
            handler.publish_result(result, callback_url, callback_topic)
        
        return result
    except Exception as e:
        logger.error(f"Command handling failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

