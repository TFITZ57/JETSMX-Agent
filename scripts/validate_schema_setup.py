#!/usr/bin/env python3
"""
Validate Airtable Schema Setup Script
Tests the schema parsing and field mapping logic without making API calls.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from setup_airtable_schema import AirtableSchemaSetup


def validate_schema_file():
    """Validate that the schema file can be parsed correctly."""
    schema_path = Path(__file__).parent.parent / "SCHEMA" / "airtable_schema.yaml"
    
    print("=" * 60)
    print("Airtable Schema Validation")
    print("=" * 60)
    print(f"Schema file: {schema_path}")
    print()
    
    # Load schema
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        print("✓ Schema file loaded successfully")
    except Exception as e:
        print(f"✗ Error loading schema: {e}")
        return False
    
    # Validate structure
    if 'airtable_base' not in schema:
        print("✗ Missing 'airtable_base' key in schema")
        return False
    print("✓ Schema has 'airtable_base' key")
    
    base_config = schema['airtable_base']
    tables = base_config.get('tables', [])
    
    if not tables:
        print("✗ No tables defined in schema")
        return False
    print(f"✓ Schema defines {len(tables)} tables")
    
    # Validate each table
    print("\nTable Validation:")
    print("-" * 60)
    
    all_table_names = set()
    basic_field_count = 0
    relationship_field_count = 0
    
    for i, table in enumerate(tables, 1):
        table_name = table.get('name', f'<unnamed-{i}>')
        all_table_names.add(table_name)
        fields = table.get('fields', [])
        
        print(f"\n{i}. {table_name}")
        print(f"   Fields: {len(fields)}")
        
        # Count field types
        basic_fields = []
        link_fields = []
        lookup_fields = []
        unknown_fields = []
        
        for field in fields:
            field_name = field.get('name', '<unnamed>')
            field_type = field.get('type', '<no-type>')
            
            # Define basic field types inline
            BASIC_FIELD_TYPES = {
                'singleLineText', 'email', 'phoneNumber', 'multilineText',
                'number', 'percent', 'currency', 'singleSelect', 'multipleSelects',
                'date', 'dateTime', 'duration', 'checkbox', 'url', 'rating',
                'richText', 'attachment', 'barcode', 'button'
            }
            RELATIONSHIP_TYPES = {'linkToAnotherRecord', 'lookup'}
            UNSUPPORTED_TYPES = {'createdTime', 'lastModifiedTime', 'createdBy', 'lastModifiedBy'}
            
            if field_type in BASIC_FIELD_TYPES:
                basic_fields.append(field_name)
            elif field_type == 'linkToAnotherRecord':
                link_fields.append(field_name)
                # Validate link configuration
                link_config = field.get('link', {})
                if 'table' not in link_config:
                    print(f"   ⚠ Link field '{field_name}' missing 'table' config")
            elif field_type == 'lookup':
                lookup_fields.append(field_name)
                # Validate lookup configuration
                lookup_config = field.get('lookup', {})
                if 'table' not in lookup_config or 'field' not in lookup_config:
                    print(f"   ⚠ Lookup field '{field_name}' missing config")
            elif field_type in UNSUPPORTED_TYPES:
                # These are auto-generated fields, skip without warning
                pass
            else:
                unknown_fields.append((field_name, field_type))
        
        print(f"   - Basic fields: {len(basic_fields)}")
        print(f"   - Link fields: {len(link_fields)}")
        print(f"   - Lookup fields: {len(lookup_fields)}")
        
        if unknown_fields:
            print(f"   ⚠ Unknown field types:")
            for fname, ftype in unknown_fields:
                print(f"     - {fname}: {ftype}")
        
        basic_field_count += len(basic_fields)
        relationship_field_count += len(link_fields) + len(lookup_fields)
    
    # Validate cross-table references
    print("\n" + "=" * 60)
    print("Cross-Table Reference Validation:")
    print("-" * 60)
    
    reference_errors = []
    for table in tables:
        table_name = table.get('name')
        for field in table.get('fields', []):
            field_name = field.get('name')
            field_type = field.get('type')
            
            # Check linkToAnotherRecord references
            if field_type == 'linkToAnotherRecord':
                link_config = field.get('link', {})
                linked_table = link_config.get('table')
                if linked_table and linked_table not in all_table_names:
                    reference_errors.append(
                        f"Table '{table_name}', field '{field_name}': "
                        f"references unknown table '{linked_table}'"
                    )
            
            # Check lookup references
            elif field_type == 'lookup':
                lookup_config = field.get('lookup', {})
                lookup_table = lookup_config.get('table')
                if lookup_table and lookup_table not in all_table_names:
                    reference_errors.append(
                        f"Table '{table_name}', field '{field_name}': "
                        f"lookup references unknown table '{lookup_table}'"
                    )
    
    if reference_errors:
        print("✗ Found cross-table reference errors:")
        for error in reference_errors:
            print(f"  - {error}")
    else:
        print("✓ All cross-table references are valid")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("-" * 60)
    print(f"Total tables: {len(tables)}")
    print(f"Total basic fields: {basic_field_count}")
    print(f"Total relationship fields: {relationship_field_count}")
    print(f"Total fields: {basic_field_count + relationship_field_count}")
    
    if reference_errors:
        print(f"\n⚠ Validation completed with {len(reference_errors)} warnings")
        return False
    else:
        print("\n✓ Validation completed successfully!")
        print("\nThe schema is ready to be applied to Airtable.")
        print("Run: python scripts/setup_airtable_schema.py")
        return True


def test_field_mapping():
    """Test the field type mapping logic."""
    print("\n" + "=" * 60)
    print("Field Mapping Tests:")
    print("-" * 60)
    
    # Create a dummy instance (won't make API calls)
    setup = AirtableSchemaSetup("dummy_key", "dummy_base")
    
    test_fields = [
        {
            'name': 'Test Text',
            'type': 'singleLineText'
        },
        {
            'name': 'Test Select',
            'type': 'singleSelect',
            'options': ['Option 1', 'Option 2', 'Option 3']
        },
        {
            'name': 'Test Multi Select',
            'type': 'multipleSelect',
            'options': ['Tag A', 'Tag B', 'Tag C']
        },
        {
            'name': 'Test Number',
            'type': 'number'
        },
    ]
    
    print("\nMapping test fields:")
    for field_def in test_fields:
        try:
            mapped = setup.map_field_type(field_def)
            print(f"✓ {field_def['name']}: {field_def['type']}")
            if 'options' in mapped:
                print(f"  Choices: {len(mapped['options']['choices'])}")
        except Exception as e:
            print(f"✗ {field_def['name']}: {e}")
            return False
    
    print("\n✓ All field mappings successful")
    return True


def main():
    """Run all validations."""
    success = True
    
    # Validate schema file
    if not validate_schema_file():
        success = False
    
    # Test field mapping
    if not test_field_mapping():
        success = False
    
    # Exit
    if success:
        print("\n" + "=" * 60)
        print("All validations passed! ✓")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("Some validations failed ✗")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()

