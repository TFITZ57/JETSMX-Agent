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

# Test fields 11-20 individually
for i in range(11, len(basic_fields)):
    field = basic_fields[i]
    try:
        table = base.create_table(
            name=f"Test Field {i}",
            fields=[{"name": "Name", "type": "singleLineText"}, field]
        )
        print(f"✓ Field {i} ({field['name']}) OK")
        # Could delete the table here to clean up, but skipping for now
    except Exception as e:
        print(f"✗ Field {i} ({field['name']}) FAILED: {e}")
        break

