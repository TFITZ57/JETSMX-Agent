"""
Enhanced bulk operations with retry and error handling.
"""
from typing import List, Dict, Any, Optional, Tuple
from tools.airtable_tools import (
    create_record,
    update_record,
    batch_create,
    batch_update
)
from shared.config.settings import get_settings
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()


class BulkOperationResult:
    """Result of a bulk operation."""
    
    def __init__(self):
        self.successful: List[Dict[str, Any]] = []
        self.failed: List[Dict[str, Any]] = []
        self.errors: List[str] = []
    
    @property
    def success_count(self) -> int:
        return len(self.successful)
    
    @property
    def failure_count(self) -> int:
        return len(self.failed)
    
    @property
    def total_count(self) -> int:
        return self.success_count + self.failure_count
    
    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return (self.success_count / self.total_count) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "successful": self.successful,
            "failed": self.failed,
            "errors": self.errors,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_count": self.total_count,
            "success_rate": round(self.success_rate, 1)
        }


def bulk_create_with_validation(
    base_id: str,
    table: str,
    records: List[Dict[str, Any]],
    batch_size: int = 10,
    validate: bool = True
) -> BulkOperationResult:
    """
    Create multiple records with validation and error handling.
    
    Args:
        base_id: Airtable base ID
        table: Table name
        records: List of record dicts with 'fields' key
        batch_size: Number of records per batch
        validate: Whether to validate before creating
        
    Returns:
        BulkOperationResult with success/failure details
    """
    result = BulkOperationResult()
    
    if not records:
        return result
    
    # Validate if requested
    if validate:
        from tools.airtable.schema import get_schema_manager
        schema = get_schema_manager()
        
        validated_records = []
        for record in records:
            fields = record.get("fields", {})
            is_valid, errors = schema.validate_record(table, fields)
            
            if is_valid:
                validated_records.append(record)
            else:
                result.failed.append(record)
                result.errors.extend(errors)
        
        records = validated_records
    
    # Process in batches
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        
        try:
            created = batch_create(base_id, table, batch)
            result.successful.extend(created)
            logger.info(f"Created batch of {len(created)} records in {table}")
        except Exception as e:
            logger.error(f"Batch create failed: {e}")
            result.failed.extend(batch)
            result.errors.append(f"Batch {i // batch_size + 1}: {str(e)}")
            
            # Try individual creates as fallback
            for record in batch:
                try:
                    created = create_record(base_id, table, record["fields"])
                    result.successful.append(created)
                    # Remove from failed if it was added
                    if record in result.failed:
                        result.failed.remove(record)
                except Exception as e2:
                    logger.error(f"Individual create failed: {e2}")
                    if record not in result.failed:
                        result.failed.append(record)
                    result.errors.append(f"Record failed: {str(e2)}")
    
    return result


def bulk_update_with_validation(
    base_id: str,
    table: str,
    updates: List[Dict[str, Any]],
    batch_size: int = 10,
    validate: bool = True,
    replace: bool = False
) -> BulkOperationResult:
    """
    Update multiple records with validation and error handling.
    
    Args:
        base_id: Airtable base ID
        table: Table name
        updates: List of dicts with 'id' and 'fields' keys
        batch_size: Number of records per batch
        validate: Whether to validate before updating
        replace: If True, replace all fields. If False, merge.
        
    Returns:
        BulkOperationResult with success/failure details
    """
    result = BulkOperationResult()
    
    if not updates:
        return result
    
    # Validate if requested
    if validate:
        from tools.airtable.schema import get_schema_manager
        schema = get_schema_manager()
        
        validated_updates = []
        for update in updates:
            fields = update.get("fields", {})
            is_valid, errors = schema.validate_record(table, fields)
            
            if is_valid:
                validated_updates.append(update)
            else:
                result.failed.append(update)
                result.errors.extend(errors)
        
        updates = validated_updates
    
    # Process in batches
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i + batch_size]
        
        try:
            updated = batch_update(base_id, table, batch, replace=replace)
            result.successful.extend(updated)
            logger.info(f"Updated batch of {len(updated)} records in {table}")
        except Exception as e:
            logger.error(f"Batch update failed: {e}")
            result.failed.extend(batch)
            result.errors.append(f"Batch {i // batch_size + 1}: {str(e)}")
            
            # Try individual updates as fallback
            for update in batch:
                try:
                    updated = update_record(
                        base_id,
                        table,
                        update["id"],
                        update["fields"],
                        replace=replace
                    )
                    result.successful.append(updated)
                    # Remove from failed if it was added
                    if update in result.failed:
                        result.failed.remove(update)
                except Exception as e2:
                    logger.error(f"Individual update failed: {e2}")
                    if update not in result.failed:
                        result.failed.append(update)
                    result.errors.append(f"Record {update.get('id')} failed: {str(e2)}")
    
    return result


def bulk_delete(
    base_id: str,
    table: str,
    record_ids: List[str],
    batch_size: int = 10
) -> BulkOperationResult:
    """
    Delete multiple records.
    
    Args:
        base_id: Airtable base ID
        table: Table name
        record_ids: List of record IDs to delete
        batch_size: Number of records per batch
        
    Returns:
        BulkOperationResult with success/failure details
    """
    from pyairtable import Api
    
    result = BulkOperationResult()
    
    if not record_ids:
        return result
    
    api = Api(settings.airtable_api_key)
    base = api.base(base_id)
    table_instance = base.table(table)
    
    # Process in batches
    for i in range(0, len(record_ids), batch_size):
        batch = record_ids[i:i + batch_size]
        
        try:
            # Airtable API supports batch delete
            deleted = table_instance.batch_delete(batch)
            for record_id in batch:
                result.successful.append({"id": record_id, "deleted": True})
            logger.info(f"Deleted batch of {len(batch)} records from {table}")
        except Exception as e:
            logger.error(f"Batch delete failed: {e}")
            result.errors.append(f"Batch {i // batch_size + 1}: {str(e)}")
            
            # Try individual deletes as fallback
            for record_id in batch:
                try:
                    table_instance.delete(record_id)
                    result.successful.append({"id": record_id, "deleted": True})
                except Exception as e2:
                    logger.error(f"Individual delete failed: {e2}")
                    result.failed.append({"id": record_id})
                    result.errors.append(f"Record {record_id} failed: {str(e2)}")
    
    return result


def upsert_records(
    base_id: str,
    table: str,
    records: List[Dict[str, Any]],
    key_field: str,
    batch_size: int = 10
) -> BulkOperationResult:
    """
    Upsert (update or insert) records based on a key field.
    
    Args:
        base_id: Airtable base ID
        table: Table name
        records: List of record dicts with 'fields' key
        key_field: Field name to use for matching existing records
        batch_size: Number of records per batch
        
    Returns:
        BulkOperationResult with success/failure details
    """
    from tools.airtable_tools import find_records
    
    result = BulkOperationResult()
    
    if not records:
        return result
    
    to_create = []
    to_update = []
    
    # Determine which records exist
    for record in records:
        fields = record.get("fields", {})
        key_value = fields.get(key_field)
        
        if not key_value:
            # No key value, must create
            to_create.append(record)
            continue
        
        # Check if exists
        try:
            formula = f"{{{key_field}}} = '{key_value}'"
            existing = find_records(base_id, table, formula=formula, max_records=1)
            
            if existing:
                # Update existing
                to_update.append({
                    "id": existing[0]["id"],
                    "fields": fields
                })
            else:
                # Create new
                to_create.append(record)
        except Exception as e:
            logger.error(f"Error checking record existence: {e}")
            result.errors.append(f"Key {key_value}: {str(e)}")
    
    # Execute creates
    if to_create:
        create_result = bulk_create_with_validation(
            base_id, table, to_create, batch_size
        )
        result.successful.extend(create_result.successful)
        result.failed.extend(create_result.failed)
        result.errors.extend(create_result.errors)
    
    # Execute updates
    if to_update:
        update_result = bulk_update_with_validation(
            base_id, table, to_update, batch_size
        )
        result.successful.extend(update_result.successful)
        result.failed.extend(update_result.failed)
        result.errors.extend(update_result.errors)
    
    return result

