"""
Webhook handler for Contractors table.

Handles contractor lifecycle events and status changes.
"""
from typing import Dict, Any
from infra.webhooks.handlers.base_handler import BaseWebhookHandler
from tools.pubsub.publisher import publish_airtable_event


class ContractorsHandler(BaseWebhookHandler):
    """Handler for Contractors table webhook events."""
    
    async def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Contractors table webhook events.
        
        Potential triggers:
        - New contractor created (from pipeline completion)
        - Status changes (Active, Paused, Inactive)
        - Compliance updates (D&A, W-9, etc.)
        - Availability updates
        
        Args:
            payload: Airtable webhook payload
            
        Returns:
            Response with actions taken
        """
        self.log_webhook_event(payload, "contractors_update")
        
        actions_taken = []
        
        # Extract table changes
        changed_tables = payload.get("changedTablesById", {})
        
        for table_id, table_data in changed_tables.items():
            table_name = table_data.get("name", "unknown")
            
            # Process changed records
            changed_records = table_data.get("changedRecordsById", {})
            for record_id, changed_record in changed_records.items():
                
                changed_fields = self.extract_changed_fields(changed_record)
                current = changed_record.get("current", {})
                
                self.logger.info(
                    f"Contractor record {record_id} updated: {changed_fields}",
                    extra={"extra_fields": {
                        "record_id": record_id,
                        "changed_fields": list(changed_fields)
                    }}
                )
                
                # Build event for downstream processing
                event_data = {
                    "source": "airtable_webhook",
                    "table_id": table_id,
                    "table_name": "contractors",
                    "record_id": record_id,
                    "changed_fields": list(changed_fields),
                    "current_values": current.get("cellValuesByFieldId", {}),
                    "timestamp": payload.get("timestamp"),
                    "webhook_id": payload.get("webhookId")
                }
                
                # Publish for potential downstream processing
                try:
                    message_id = publish_airtable_event(event_data)
                    actions_taken.append({
                        "action": "published_to_pubsub",
                        "record_id": record_id,
                        "message_id": message_id
                    })
                except Exception as e:
                    self.logger.error(f"Failed to publish event: {str(e)}")
                    actions_taken.append({
                        "action": "pubsub_failed",
                        "record_id": record_id,
                        "error": str(e)
                    })
            
            # Process created records
            created_records = table_data.get("createdRecordsById", {})
            for record_id, created_record in created_records.items():
                self.logger.info(f"New contractor record created: {record_id}")
                
                # Publish contractor creation event
                event_data = {
                    "source": "airtable_webhook",
                    "table_id": table_id,
                    "table_name": "contractors",
                    "record_id": record_id,
                    "event_type": "contractor_created",
                    "timestamp": payload.get("timestamp"),
                    "webhook_id": payload.get("webhookId")
                }
                
                try:
                    message_id = publish_airtable_event(event_data)
                    actions_taken.append({
                        "action": "contractor_created",
                        "record_id": record_id,
                        "message_id": message_id
                    })
                except Exception as e:
                    self.logger.error(f"Failed to publish contractor creation: {str(e)}")
                    actions_taken.append({
                        "action": "pubsub_failed",
                        "record_id": record_id,
                        "error": str(e)
                    })
        
        return {
            "status": "processed",
            "actions_taken": actions_taken,
            "webhook_id": payload.get("webhookId")
        }

