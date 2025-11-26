"""
Schema introspection and validation for Airtable.
"""
from typing import Dict, List, Any, Optional
import yaml
from pathlib import Path
from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


class SchemaManager:
    """Manage Airtable schema information."""
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize schema manager.
        
        Args:
            schema_path: Path to airtable_schema.yaml file
        """
        if schema_path is None:
            # Default to project schema
            schema_path = Path(__file__).parent.parent.parent / "schema" / "airtable_schema.yaml"
        
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load schema from YAML file."""
        try:
            with open(self.schema_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            return {}
    
    def get_tables(self) -> List[str]:
        """Get list of all table names."""
        tables = self.schema.get("airtable_base", {}).get("tables", [])
        return [t.get("name") for t in tables]
    
    def get_table_config(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific table."""
        tables = self.schema.get("airtable_base", {}).get("tables", [])
        
        for table in tables:
            if table.get("name") == table_name or table.get("api_name") == table_name:
                return table
        
        return None
    
    def get_fields(self, table_name: str) -> List[Dict[str, Any]]:
        """Get list of fields for a table."""
        table = self.get_table_config(table_name)
        if table:
            return table.get("fields", [])
        return []
    
    def get_field_config(self, table_name: str, field_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific field."""
        fields = self.get_fields(table_name)
        
        for field in fields:
            if field.get("name") == field_name or field.get("api_name") == field_name:
                return field
        
        return None
    
    def get_field_type(self, table_name: str, field_name: str) -> Optional[str]:
        """Get the type of a field."""
        field = self.get_field_config(table_name, field_name)
        if field:
            return field.get("type")
        return None
    
    def get_primary_key(self, table_name: str) -> Optional[str]:
        """Get the primary key field name for a table."""
        fields = self.get_fields(table_name)
        
        for field in fields:
            if field.get("is_primary"):
                return field.get("name")
        
        return None
    
    def get_searchable_fields(self, table_name: str) -> List[str]:
        """Get list of searchable field names for a table."""
        # Check agent config first if it exists
        try:
            config_path = Path(__file__).parent.parent / "airtable" / "config.yaml"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    tables = config.get("tables", {})
                    table_key = table_name.lower().replace(" ", "_")
                    if table_key in tables:
                        return tables[table_key].get("searchable_fields", [])
        except:
            pass
        
        # Fall back to all text fields
        fields = self.get_fields(table_name)
        searchable = []
        
        text_types = ["singleLineText", "longText", "email", "phoneNumber"]
        
        for field in fields:
            if field.get("type") in text_types:
                searchable.append(field.get("name"))
        
        return searchable
    
    def get_linked_table(self, table_name: str, field_name: str) -> Optional[str]:
        """Get the linked table name for a linkToAnotherRecord field."""
        field = self.get_field_config(table_name, field_name)
        
        if field and field.get("type") == "linkToAnotherRecord":
            link_info = field.get("link", {})
            return link_info.get("table")
        
        return None
    
    def validate_field_value(
        self,
        table_name: str,
        field_name: str,
        value: Any
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a field value against schema.
        
        Returns:
            (is_valid, error_message)
        """
        field = self.get_field_config(table_name, field_name)
        
        if not field:
            return (False, f"Field '{field_name}' not found in table '{table_name}'")
        
        field_type = field.get("type")
        
        # Type validation
        if field_type == "checkbox" and not isinstance(value, bool):
            return (False, f"Field '{field_name}' must be boolean")
        
        if field_type == "number" and not isinstance(value, (int, float)):
            return (False, f"Field '{field_name}' must be numeric")
        
        if field_type == "email" and not isinstance(value, str):
            return (False, f"Field '{field_name}' must be string")
        
        if field_type == "singleSelect":
            options = field.get("options", [])
            if options and value not in options:
                return (False, f"Field '{field_name}' must be one of: {options}")
        
        if field_type == "multipleSelect":
            options = field.get("options", [])
            if options and isinstance(value, list):
                invalid = [v for v in value if v not in options]
                if invalid:
                    return (False, f"Invalid options for '{field_name}': {invalid}")
        
        return (True, None)
    
    def validate_record(
        self,
        table_name: str,
        fields: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Validate all fields in a record.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        for field_name, value in fields.items():
            is_valid, error = self.validate_field_value(table_name, field_name, value)
            if not is_valid:
                errors.append(error)
        
        return (len(errors) == 0, errors)
    
    def get_table_api_name(self, display_name: str) -> Optional[str]:
        """Convert display name to API name."""
        table = self.get_table_config(display_name)
        if table:
            return table.get("api_name", display_name)
        return display_name
    
    def get_field_api_name(self, table_name: str, display_name: str) -> Optional[str]:
        """Convert field display name to API name."""
        field = self.get_field_config(table_name, display_name)
        if field:
            return field.get("api_name", display_name)
        return display_name
    
    def describe_table(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get full description of table structure."""
        table = self.get_table_config(table_name)
        if not table:
            return None
        
        description = {
            "name": table.get("name"),
            "api_name": table.get("api_name"),
            "description": table.get("description"),
            "field_count": len(table.get("fields", [])),
            "fields": []
        }
        
        for field in table.get("fields", []):
            field_desc = {
                "name": field.get("name"),
                "api_name": field.get("api_name"),
                "type": field.get("type"),
                "is_primary": field.get("is_primary", False)
            }
            
            if field.get("type") == "singleSelect" or field.get("type") == "multipleSelect":
                field_desc["options"] = field.get("options", [])
            
            if field.get("type") == "linkToAnotherRecord":
                field_desc["linked_table"] = field.get("link", {}).get("table")
            
            description["fields"].append(field_desc)
        
        return description
    
    def describe_all_tables(self) -> List[Dict[str, Any]]:
        """Get descriptions of all tables."""
        tables = self.get_tables()
        return [self.describe_table(t) for t in tables if self.describe_table(t)]


# Global instance
_schema_manager = None


def get_schema_manager() -> SchemaManager:
    """Get or create global schema manager instance."""
    global _schema_manager
    if _schema_manager is None:
        _schema_manager = SchemaManager()
    return _schema_manager

