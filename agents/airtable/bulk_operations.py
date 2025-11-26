"""
Bulk operation handlers for the Airtable agent.
"""
from typing import List, Dict, Any, Optional
from tools.airtable.bulk import (
    bulk_create_with_validation,
    bulk_update_with_validation,
    bulk_delete,
    upsert_records,
    BulkOperationResult
)
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger
from shared.logging.audit import log_audit_event

logger = setup_logger(__name__)
settings = get_settings()


class BulkOperationManager:
    """Manage bulk operations with audit logging and validation."""
    
    def __init__(self, base_id: Optional[str] = None):
        """
        Initialize bulk operation manager.
        
        Args:
            base_id: Airtable base ID (defaults to settings)
        """
        self.base_id = base_id or settings.airtable_base_id
    
    def create_many(
        self,
        table: str,
        records: List[Dict[str, Any]],
        batch_size: int = 10,
        validate: bool = True,
        initiated_by: str = "airtable_agent",
        reason: str = "Bulk create operation"
    ) -> BulkOperationResult:
        """
        Create multiple records.
        
        Args:
            table: Table name
            records: List of record dicts with 'fields' key
            batch_size: Records per batch
            validate: Whether to validate before creating
            initiated_by: Who initiated this operation
            reason: Reason for bulk create
            
        Returns:
            BulkOperationResult
        """
        logger.info(f"Bulk create: {len(records)} records in {table}")
        
        # Audit log
        log_audit_event(
            action="bulk_create",
            resource_type="airtable_record",
            resource_id=f"{table}:bulk",
            initiated_by=initiated_by,
            details={
                "table": table,
                "record_count": len(records),
                "reason": reason
            }
        )
        
        result = bulk_create_with_validation(
            self.base_id,
            table,
            records,
            batch_size=batch_size,
            validate=validate
        )
        
        logger.info(
            f"Bulk create complete: {result.success_count}/{result.total_count} successful"
        )
        
        return result
    
    def update_many(
        self,
        table: str,
        updates: List[Dict[str, Any]],
        batch_size: int = 10,
        validate: bool = True,
        replace: bool = False,
        initiated_by: str = "airtable_agent",
        reason: str = "Bulk update operation"
    ) -> BulkOperationResult:
        """
        Update multiple records.
        
        Args:
            table: Table name
            updates: List of dicts with 'id' and 'fields' keys
            batch_size: Records per batch
            validate: Whether to validate before updating
            replace: If True, replace all fields. If False, merge.
            initiated_by: Who initiated this operation
            reason: Reason for bulk update
            
        Returns:
            BulkOperationResult
        """
        logger.info(f"Bulk update: {len(updates)} records in {table}")
        
        # Audit log
        log_audit_event(
            action="bulk_update",
            resource_type="airtable_record",
            resource_id=f"{table}:bulk",
            initiated_by=initiated_by,
            details={
                "table": table,
                "record_count": len(updates),
                "replace": replace,
                "reason": reason
            }
        )
        
        result = bulk_update_with_validation(
            self.base_id,
            table,
            updates,
            batch_size=batch_size,
            validate=validate,
            replace=replace
        )
        
        logger.info(
            f"Bulk update complete: {result.success_count}/{result.total_count} successful"
        )
        
        return result
    
    def delete_many(
        self,
        table: str,
        record_ids: List[str],
        batch_size: int = 10,
        initiated_by: str = "airtable_agent",
        reason: str = "Bulk delete operation"
    ) -> BulkOperationResult:
        """
        Delete multiple records.
        
        Args:
            table: Table name
            record_ids: List of record IDs to delete
            batch_size: Records per batch
            initiated_by: Who initiated this operation
            reason: Reason for bulk delete
            
        Returns:
            BulkOperationResult
        """
        logger.warning(f"Bulk delete: {len(record_ids)} records in {table}")
        
        # Audit log - important for deletes
        log_audit_event(
            action="bulk_delete",
            resource_type="airtable_record",
            resource_id=f"{table}:bulk",
            initiated_by=initiated_by,
            details={
                "table": table,
                "record_count": len(record_ids),
                "record_ids": record_ids[:100],  # Log first 100 IDs
                "reason": reason
            },
            severity="high"
        )
        
        result = bulk_delete(
            self.base_id,
            table,
            record_ids,
            batch_size=batch_size
        )
        
        logger.info(
            f"Bulk delete complete: {result.success_count}/{result.total_count} successful"
        )
        
        return result
    
    def upsert_many(
        self,
        table: str,
        records: List[Dict[str, Any]],
        key_field: str,
        batch_size: int = 10,
        initiated_by: str = "airtable_agent",
        reason: str = "Bulk upsert operation"
    ) -> BulkOperationResult:
        """
        Upsert (update or insert) multiple records.
        
        Args:
            table: Table name
            records: List of record dicts with 'fields' key
            key_field: Field to use for matching
            batch_size: Records per batch
            initiated_by: Who initiated this operation
            reason: Reason for bulk upsert
            
        Returns:
            BulkOperationResult
        """
        logger.info(f"Bulk upsert: {len(records)} records in {table} on {key_field}")
        
        # Audit log
        log_audit_event(
            action="bulk_upsert",
            resource_type="airtable_record",
            resource_id=f"{table}:bulk",
            initiated_by=initiated_by,
            details={
                "table": table,
                "record_count": len(records),
                "key_field": key_field,
                "reason": reason
            }
        )
        
        result = upsert_records(
            self.base_id,
            table,
            records,
            key_field=key_field,
            batch_size=batch_size
        )
        
        logger.info(
            f"Bulk upsert complete: {result.success_count}/{result.total_count} successful"
        )
        
        return result
    
    def validate_bulk_operation(
        self,
        operation: str,
        table: str,
        record_count: int,
        max_batch_size: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a bulk operation before execution.
        
        Args:
            operation: Operation type ("create", "update", "delete")
            table: Table name
            record_count: Number of records
            max_batch_size: Max allowed batch size
            
        Returns:
            (is_valid, error_message)
        """
        if max_batch_size is None:
            max_batch_size = 1000
        
        if record_count == 0:
            return (False, "No records provided")
        
        if record_count > max_batch_size:
            return (
                False,
                f"Batch size {record_count} exceeds maximum {max_batch_size}"
            )
        
        # Check if table exists in schema
        from tools.airtable.schema import get_schema_manager
        schema = get_schema_manager()
        
        if table not in schema.get_tables():
            return (False, f"Table '{table}' not found in schema")
        
        # Additional validation for sensitive operations
        if operation == "delete" and record_count > 100:
            logger.warning(f"Large delete operation: {record_count} records")
            # Could require additional confirmation here
        
        return (True, None)

