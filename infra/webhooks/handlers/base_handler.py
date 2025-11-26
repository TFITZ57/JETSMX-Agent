"""
Base webhook handler with common utilities.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


class BaseWebhookHandler(ABC):
    """Base class for Airtable webhook handlers."""
    
    def __init__(self):
        """Initialize handler."""
        self.logger = setup_logger(self.__class__.__name__)
    
    @abstractmethod
    async def handle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle webhook payload.
        
        Args:
            payload: Airtable webhook payload
            
        Returns:
            Response dict with actions taken
        """
        pass
    
    def extract_changed_fields(
        self,
        changed_record: Dict[str, Any]
    ) -> Set[str]:
        """
        Extract field names that changed in a record.
        
        Args:
            changed_record: Record object from changedRecordsById
            
        Returns:
            Set of field names that changed
        """
        changed_fields = set()
        
        # Current values
        if "current" in changed_record and "cellValuesByFieldId" in changed_record["current"]:
            changed_fields.update(changed_record["current"]["cellValuesByFieldId"].keys())
        
        # Previous values
        if "previous" in changed_record and "cellValuesByFieldId" in changed_record["previous"]:
            changed_fields.update(changed_record["previous"]["cellValuesByFieldId"].keys())
        
        return changed_fields
    
    def get_field_value(
        self,
        record: Dict[str, Any],
        field_id: str,
        field_name_map: Dict[str, str]
    ) -> Any:
        """
        Get field value from record by field ID.
        
        Args:
            record: Record object with cellValuesByFieldId
            field_id: Field ID
            field_name_map: Mapping of field IDs to field names
            
        Returns:
            Field value or None
        """
        if "cellValuesByFieldId" not in record:
            return None
        
        return record["cellValuesByFieldId"].get(field_id)
    
    def get_field_changes(
        self,
        changed_record: Dict[str, Any],
        field_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get before/after values for a specific field.
        
        Args:
            changed_record: Record object from changedRecordsById
            field_id: Field ID to check
            
        Returns:
            Dict with 'previous' and 'current' values, or None if field didn't change
        """
        previous_val = None
        current_val = None
        
        if "previous" in changed_record and "cellValuesByFieldId" in changed_record["previous"]:
            previous_val = changed_record["previous"]["cellValuesByFieldId"].get(field_id)
        
        if "current" in changed_record and "cellValuesByFieldId" in changed_record["current"]:
            current_val = changed_record["current"]["cellValuesByFieldId"].get(field_id)
        
        # Only return if there was an actual change
        if previous_val != current_val:
            return {
                "previous": previous_val,
                "current": current_val
            }
        
        return None
    
    def check_condition(
        self,
        changed_record: Dict[str, Any],
        field_id: str,
        expected_value: Any
    ) -> bool:
        """
        Check if a field matches expected value after change.
        
        Args:
            changed_record: Record object from changedRecordsById
            field_id: Field ID to check
            expected_value: Expected value
            
        Returns:
            True if field now equals expected value
        """
        if "current" not in changed_record:
            return False
        
        current = changed_record.get("current", {})
        field_values = current.get("cellValuesByFieldId", {})
        
        return field_values.get(field_id) == expected_value
    
    def get_record_id(self, changed_record: Dict[str, Any]) -> Optional[str]:
        """
        Extract record ID from changed record.
        
        Args:
            changed_record: Record object from changedRecordsById
            
        Returns:
            Record ID or None
        """
        return changed_record.get("current", {}).get("id") or \
               changed_record.get("previous", {}).get("id")
    
    def extract_table_changes(
        self,
        payload: Dict[str, Any],
        table_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract changes for a specific table from webhook payload.
        
        Args:
            payload: Full webhook payload
            table_id: Table ID to extract
            
        Returns:
            Table changes object or None
        """
        changed_tables = payload.get("changedTablesById", {})
        return changed_tables.get(table_id)
    
    def log_webhook_event(
        self,
        payload: Dict[str, Any],
        action: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log webhook event with structured data.
        
        Args:
            payload: Webhook payload
            action: Action being taken
            details: Additional details to log
        """
        extra_fields = {
            "webhook_id": payload.get("webhookId"),
            "base_id": payload.get("baseId"),
            "timestamp": payload.get("timestamp"),
            "action": action
        }
        
        if details:
            extra_fields.update(details)
        
        self.logger.info(
            f"Processing webhook: {action}",
            extra={"extra_fields": extra_fields}
        )







