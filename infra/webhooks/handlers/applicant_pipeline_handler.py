"""
Webhook handler for Applicant Pipeline table.

Handles pipeline stage transitions, screening approvals, background checks, etc.
"""
from typing import Dict, Any
from infra.webhooks.handlers.base_handler import BaseWebhookHandler
from tools.pubsub.publisher import publish_airtable_event


class ApplicantPipelineHandler(BaseWebhookHandler):
    """Handler for Applicant Pipeline webhook events."""
    
    # Field name mappings (for readability - actual handling uses field IDs)
    PIPELINE_STAGE_FIELD = "Pipeline Stage"
    SCREENING_DECISION_FIELD = "Screening Decision"
    BACKGROUND_CHECK_STATUS_FIELD = "Background Check Status"
    EMAIL_DRAFT_GENERATED_FIELD = "Email Draft Generated?"
    CONTRACTOR_CREATED_FIELD = "Contractor Created?"
    
    async def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Applicant Pipeline webhook events.
        
        Key triggers:
        - Screening Decision = "Approve" -> Generate outreach email draft
        - Pipeline Stage = "Interview Complete" -> Post-interview decision
        - Background Check Status = "Passed" -> Create contractor record
        
        Args:
            payload: Airtable webhook payload
            
        Returns:
            Response with actions taken
        """
        self.log_webhook_event(payload, "applicant_pipeline_update")
        
        actions_taken = []
        
        # Extract table changes
        changed_tables = payload.get("changedTablesById", {})
        
        # Process each changed table (should be applicant_pipeline)
        for table_id, table_data in changed_tables.items():
            table_name = table_data.get("name", "unknown")
            
            # Process changed records
            changed_records = table_data.get("changedRecordsById", {})
            for record_id, changed_record in changed_records.items():
                
                actions = await self._process_pipeline_record(
                    payload,
                    table_id,
                    record_id,
                    changed_record
                )
                actions_taken.extend(actions)
            
            # Process created records
            created_records = table_data.get("createdRecordsById", {})
            for record_id, created_record in created_records.items():
                self.logger.info(f"New pipeline record created: {record_id}")
                actions_taken.append({
                    "action": "record_created",
                    "record_id": record_id,
                    "table": table_name
                })
        
        return {
            "status": "processed",
            "actions_taken": actions_taken,
            "webhook_id": payload.get("webhookId")
        }
    
    async def _process_pipeline_record(
        self,
        payload: Dict[str, Any],
        table_id: str,
        record_id: str,
        changed_record: Dict[str, Any]
    ) -> list:
        """
        Process a single pipeline record change.
        
        Args:
            payload: Full webhook payload
            table_id: Table ID
            record_id: Record ID
            changed_record: Changed record data
            
        Returns:
            List of actions taken
        """
        actions = []
        changed_fields = self.extract_changed_fields(changed_record)
        
        self.logger.info(
            f"Processing pipeline record {record_id}, changed fields: {changed_fields}",
            extra={"extra_fields": {
                "record_id": record_id,
                "changed_fields": list(changed_fields)
            }}
        )
        
        # Get current field values
        current = changed_record.get("current", {})
        cell_values = current.get("cellValuesByFieldId", {})
        
        # Build event data for downstream processing
        event_data = {
            "source": "airtable_webhook",
            "table_id": table_id,
            "table_name": "applicant_pipeline",
            "record_id": record_id,
            "changed_fields": list(changed_fields),
            "current_values": cell_values,
            "timestamp": payload.get("timestamp"),
            "webhook_id": payload.get("webhookId")
        }
        
        # Publish to Pub/Sub for async processing by agents
        try:
            message_id = publish_airtable_event(event_data)
            actions.append({
                "action": "published_to_pubsub",
                "record_id": record_id,
                "message_id": message_id,
                "topic": "jetsmx-airtable-events"
            })
            self.logger.info(f"Published pipeline event to Pub/Sub: {message_id}")
        except Exception as e:
            self.logger.error(f"Failed to publish to Pub/Sub: {str(e)}")
            actions.append({
                "action": "pubsub_failed",
                "record_id": record_id,
                "error": str(e)
            })
        
        return actions







