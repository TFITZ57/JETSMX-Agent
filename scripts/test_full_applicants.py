from pyairtable import Api
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
import yaml

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()
api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')

api = Api(api_key)
base = api.base(base_id)

from scripts.setup_airtable_schema import AirtableSchemaSetup

setup = AirtableSchemaSetup(api_key, base_id)

# Load schema
with open('SCHEMA/airtable_schema.yaml', 'r') as f:
    schema = yaml.safe_load(f)

# Get Applicants table
applicants_table = schema['airtable_base']['tables'][0]
fields = applicants_table['fields']

# Get only basic fields
basic_fields = [setup.map_field_type(f) for f in fields if setup.is_basic_field(f)]

print(f"Creating table with {len(basic_fields)} fields")
print("Fields:", [f['name'] for f in basic_fields])

# Test first half
try:
    table1 = base.create_table(
        name="Applicants First Half",
        fields=basic_fields[:11]
    )
    print(f"\n✓ Success with first 11! Created table: {table1.id}")
except Exception as e:
    print(f"\n✗ Error with first 11: {e}")

# Test second half
try:
    table2 = base.create_table(
        name="Applicants Second Half",
        fields=[{"name": "Name", "type": "singleLineText"}] + basic_fields[11:]
    )
    print(f"\n✓ Success with last 10! Created table: {table2.id}")
except Exception as e:
    print(f"\n✗ Error with last 10: {e}")

