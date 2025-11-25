"""
Webhook handler for Interactions table.

Handles interaction logging and audit trail updates.
"""
from typing import Dict, Any
from infra.webhooks.handlers.base_handler import BaseWebhookHandler


class InteractionsHandler(BaseWebhookHandler):
    """Handler for Interactions table webhook events."""
    
    async def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Interactions table webhook events.
        
        This table is primarily an audit log, so most events are informational.
        We track when interactions are created but typically don't trigger workflows.
        
        Args:
            payload: Airtable webhook payload
            
        Returns:
            Response with actions taken
        """
        self.log_webhook_event(payload, "interactions_update")
        
        actions_taken = []
        
        # Extract table changes
        changed_tables = payload.get("changedTablesById", {})
        
        for table_id, table_data in changed_tables.items():
            table_name = table_data.get("name", "unknown")
            
            # Process created records (most common for audit log)
            created_records = table_data.get("createdRecordsById", {})
            for record_id, created_record in created_records.items():
                cell_values = created_record.get("cellValuesByFieldId", {})
                
                self.logger.info(
                    f"New interaction logged: {record_id}",
                    extra={"extra_fields": {
                        "record_id": record_id,
                        "table": table_name
                    }}
                )
                
                actions_taken.append({
                    "action": "interaction_logged",
                    "record_id": record_id,
                    "table": table_name
                })
            
            # Process changed records (less common, but track it)
            changed_records = table_data.get("changedRecordsById", {})
            for record_id, changed_record in changed_records.items():
                changed_fields = self.extract_changed_fields(changed_record)
                
                self.logger.info(
                    f"Interaction record {record_id} updated: {changed_fields}",
                    extra={"extra_fields": {
                        "record_id": record_id,
                        "changed_fields": list(changed_fields)
                    }}
                )
                
                actions_taken.append({
                    "action": "interaction_updated",
                    "record_id": record_id,
                    "changed_fields": list(changed_fields)
                })
        
        return {
            "status": "processed",
            "actions_taken": actions_taken,
            "webhook_id": payload.get("webhookId")
        }

