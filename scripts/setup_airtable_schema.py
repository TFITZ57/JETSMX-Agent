#!/usr/bin/env python3
"""
Airtable Schema Setup Script

Reads SCHEMA/airtable_schema.yaml and creates all tables and fields
in an Airtable base using the Airtable Meta API.

Usage:
    python scripts/setup_airtable_schema.py [--base-id BASE_ID]
    
If --base-id is not provided, it will use AIRTABLE_BASE_ID from .env
The base must already exist (Airtable API doesn't support base creation).
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.logging.logger import setup_logger

logger = setup_logger(__name__)


class AirtableSchemaSetup:
    """Handle Airtable schema setup via Meta API."""
    
    # Field types that require special handling
    RELATIONSHIP_TYPES = {'linkToAnotherRecord', 'lookup'}
    # These fields cannot be created via API
    UNSUPPORTED_TYPES = {'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy'}
    
    def __init__(self, api_key: str, base_id: str):
        self.api_key = api_key
        self.base_id = base_id
        from pyairtable import Api
        import requests
        self.api = Api(api_key)
        self.base = self.api.base(base_id)
        self.requests = requests
        self.base_url = "https://api.airtable.com/v0/meta/bases"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.table_id_map: Dict[str, str] = {}  # table name -> table ID
        self.field_id_map: Dict[str, Dict[str, str]] = {}  # table name -> {field name -> field ID}
        
    def get_existing_tables(self) -> Dict[str, Dict[str, Any]]:
        """Get all existing tables and their fields."""
        logger.info(f"Fetching existing tables from base {self.base_id}")
        
        schema = self.base.schema()
        tables = {}
        
        for table in schema.tables:
            table_name = table.name
            tables[table_name] = table
            self.table_id_map[table_name] = table.id
            
            # Store field IDs
            self.field_id_map[table_name] = {}
            for field in table.fields:
                self.field_id_map[table_name][field.name] = field.id
                
        logger.info(f"Found {len(tables)} existing tables: {list(tables.keys())}")
        return tables
    
    def parse_schema(self, schema_path: str) -> Dict[str, Any]:
        """Parse the YAML schema file."""
        logger.info(f"Parsing schema from {schema_path}")
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        return schema
    
    def map_field_type(self, field: Dict[str, Any]) -> Dict[str, Any]:
        """Map YAML field definition to Airtable API field spec."""
        field_type = field['type']
        
        # Map YAML types to Airtable API types
        type_mapping = {
            'longText': 'multilineText',  # YAML uses longText, API uses multilineText
            'multipleSelect': 'multipleSelects'  # YAML uses multipleSelect, API uses multipleSelects
        }
        api_type = type_mapping.get(field_type, field_type)
        
        field_spec = {
            'name': field['name'],
            'type': api_type
        }
        
        # Handle different field types
        if api_type == 'singleSelect':
            field_spec['options'] = {
                'choices': [{'name': opt} for opt in field.get('options', [])]
            }
        elif api_type == 'multipleSelects':
            field_spec['options'] = {
                'choices': [{'name': opt} for opt in field.get('options', [])]
            }
        elif api_type == 'number':
            field_spec['options'] = {'precision': 0}  # Default to integer
        elif api_type == 'checkbox':
            field_spec['options'] = {
                'icon': 'check',
                'color': 'greenBright'
            }
        elif api_type == 'date':
            field_spec['options'] = {
                'dateFormat': {'name': 'local', 'format': 'l'}
            }
        elif api_type == 'dateTime':
            field_spec['options'] = {
                'dateFormat': {'name': 'local', 'format': 'l'},
                'timeFormat': {'name': '12hour', 'format': 'h:mma'},
                'timeZone': 'client'
            }
        # createdTime and lastModifiedTime don't need options in initial creation
        
        return field_spec
    
    def is_basic_field(self, field: Dict[str, Any]) -> bool:
        """Check if field is a basic field (not relationship, lookup, or unsupported)."""
        field_type = field['type']
        return field_type not in self.RELATIONSHIP_TYPES and field_type not in self.UNSUPPORTED_TYPES
    
    def create_table(self, table_name: str, description: str, fields: List[Dict[str, Any]]) -> str:
        """Create a table with basic fields only."""
        # Only include basic fields in initial creation
        basic_fields = [
            self.map_field_type(f) for f in fields 
            if self.is_basic_field(f)
        ]
        
        # Log skipped fields
        skipped = [f['name'] for f in fields if not self.is_basic_field(f)]
        if skipped:
            logger.info(f"  Skipping {len(skipped)} fields for later: {', '.join(skipped[:3])}{'...' if len(skipped) > 3 else ''}")
        
        # Ensure first field is a valid primary field type (text-based)
        # Primary fields can be: singleLineText, email, phoneNumber, url, autoNumber
        valid_primary_types = {'singleLineText', 'email', 'phoneNumber', 'url', 'autoNumber'}
        
        if basic_fields and basic_fields[0]['type'] not in valid_primary_types:
            # Find a text-based field to move to the front
            text_field_idx = next((i for i, f in enumerate(basic_fields) if f['type'] in valid_primary_types), None)
            if text_field_idx:
                # Move the text field to the front
                basic_fields.insert(0, basic_fields.pop(text_field_idx))
                logger.info(f"  Reordered fields to make '{basic_fields[0]['name']}' the primary field")
            else:
                # No text field found - add a default ID field
                basic_fields.insert(0, {'name': 'ID', 'type': 'autoNumber', 'options': {}})
                logger.info(f"  Added auto-number 'ID' field as primary field")
        
        logger.info(f"Creating table '{table_name}' with {len(basic_fields)} basic fields")
        logger.debug(f"Fields being created: {[f['name'] + ':' + f['type'] for f in basic_fields]}")
        
        # Use pyairtable's create_table method
        table = self.base.create_table(
            name=table_name,
            fields=basic_fields,
            description=description
        )
        
        table_id = table.id
        self.table_id_map[table_name] = table_id
        
        # Refresh schema to get field IDs
        schema = self.base.schema()
        for table_schema in schema.tables:
            if table_schema.name == table_name:
                self.field_id_map[table_name] = {}
                for field in table_schema.fields:
                    self.field_id_map[table_name][field.name] = field.id
                break
        
        logger.info(f"✓ Created table '{table_name}' (ID: {table_id})")
        return table_id
    
    def add_relationship_field(self, table_name: str, field: Dict[str, Any]) -> bool:
        """Add a relationship or lookup field to an existing table."""
        table_id = self.table_id_map.get(table_name)
        if not table_id:
            logger.error(f"Table '{table_name}' not found in table ID map")
            return False
        
        field_type = field['type']
        field_name = field['name']
        
        # Check if field already exists
        if field_name in self.field_id_map.get(table_name, {}):
            logger.info(f"  Field '{field_name}' already exists in '{table_name}', skipping")
            return True
        
        url = f"{self.base_url}/{self.base_id}/tables/{table_id}/fields"
        
        if field_type == 'linkToAnotherRecord':
            linked_table_name = field['link']['table']
            linked_table_id = self.table_id_map.get(linked_table_name)
            
            if not linked_table_id:
                logger.error(f"Linked table '{linked_table_name}' not found")
                return False
            
            # Note: prefersSingleRecordLink and isReversed options may not be supported
            # when adding fields via API. These can be configured manually in Airtable UI.
            field_spec = {
                'name': field_name,
                'type': 'multipleRecordLinks',
                'options': {
                    'linkedTableId': linked_table_id
                }
            }
            
        elif field_type == 'lookup':
            # Lookup field requires a linked record field to look through
            lookup_config = field.get('lookup', {})
            linked_table_name = lookup_config.get('table')
            lookup_field_name = lookup_config.get('field')
            
            # Find the linked record field in the current table that points to the lookup table
            # This is a simplification - in practice, we need to find which linkToAnotherRecord field
            # points to the target table
            linked_record_field_id = None
            
            # Search for a linkToAnotherRecord field that points to the target table
            for fname, fid in self.field_id_map.get(table_name, {}).items():
                # We'd need to check the field definition, but for now we'll skip lookups
                pass
            
            # Lookups are complex - skip for now and log
            logger.warning(f"⚠ Skipping lookup field '{field_name}' - requires manual configuration")
            return True
        
        else:
            logger.error(f"Unknown relationship field type: {field_type}")
            return False
        
        logger.info(f"  Adding {field_type} field '{field_name}' to '{table_name}'")
        response = self.requests.post(url, headers=self.headers, json=field_spec)
        
        if response.status_code == 200:
            result = response.json()
            self.field_id_map[table_name][field_name] = result['id']
            logger.info(f"  ✓ Added field '{field_name}'")
            return True
        else:
            logger.error(f"  ✗ Failed to add field '{field_name}': {response.text}")
            return False
    
    def setup_schema(self, schema_path: str) -> bool:
        """Main method to set up the entire schema."""
        try:
            # Parse schema
            schema = self.parse_schema(schema_path)
            base_config = schema.get('airtable_base', {})
            tables = base_config.get('tables', [])
            
            logger.info(f"Setting up schema with {len(tables)} tables")
            
            # Get existing tables
            existing_tables = self.get_existing_tables()
            
            # PASS 1: Create tables with basic fields
            logger.info("\n=== PASS 1: Creating tables with basic fields ===")
            for table in tables:
                table_name = table['name']
                
                if table_name in existing_tables:
                    logger.info(f"⊙ Table '{table_name}' already exists, skipping")
                    continue
                
                description = table.get('description', '')
                fields = table.get('fields', [])
                
                try:
                    self.create_table(table_name, description, fields)
                except Exception as e:
                    logger.error(f"✗ Failed to create table '{table_name}': {e}")
                    return False
            
            # PASS 2: Add relationship fields
            logger.info("\n=== PASS 2: Adding relationship fields ===")
            for table in tables:
                table_name = table['name']
                fields = table.get('fields', [])
                
                relationship_fields = [f for f in fields if not self.is_basic_field(f)]
                
                if not relationship_fields:
                    continue
                
                logger.info(f"\nProcessing relationships for '{table_name}'")
                for field in relationship_fields:
                    try:
                        self.add_relationship_field(table_name, field)
                    except Exception as e:
                        logger.error(f"  ✗ Failed to add field '{field['name']}': {e}")
            
            logger.info("\n=== Schema Setup Complete ===")
            logger.info(f"Tables created/verified: {len(self.table_id_map)}")
            return True
            
        except Exception as e:
            logger.error(f"Schema setup failed: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Set up Airtable schema from YAML definition"
    )
    parser.add_argument(
        '--base-id',
        help='Airtable base ID (overrides .env)',
        default=None
    )
    parser.add_argument(
        '--schema',
        help='Path to schema YAML file',
        default='SCHEMA/airtable_schema.yaml'
    )
    args = parser.parse_args()
    
    # Load environment
    load_dotenv()
    
    # Get credentials
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = args.base_id or os.getenv('AIRTABLE_BASE_ID')
    
    if not api_key:
        logger.error("AIRTABLE_API_KEY not found in environment")
        sys.exit(1)
    
    if not base_id:
        logger.error("Base ID not provided. Use --base-id or set AIRTABLE_BASE_ID in .env")
        logger.info("Note: You must create the base manually in Airtable first")
        sys.exit(1)
    
    if base_id == "YOUR_AIRTABLE_BASE_ID_HERE":
        logger.error("Please create an Airtable base and update AIRTABLE_BASE_ID in .env")
        sys.exit(1)
    
    # Resolve schema path
    schema_path = Path(args.schema)
    if not schema_path.is_absolute():
        schema_path = project_root / schema_path
    
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)
    
    # Run setup
    logger.info(f"Setting up Airtable base: {base_id}")
    logger.info(f"Using schema: {schema_path}")
    
    setup = AirtableSchemaSetup(api_key, base_id)
    success = setup.setup_schema(str(schema_path))
    
    if success:
        logger.info("\n✓ Schema setup completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Check your Airtable base to verify tables and fields")
        logger.info("2. Lookup fields may need manual configuration")
        logger.info("3. Update any automation triggers in Airtable")
        sys.exit(0)
    else:
        logger.error("\n✗ Schema setup failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
