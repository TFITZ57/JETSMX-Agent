from pyairtable import Api
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()
api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')

api = Api(api_key)
base = api.base(base_id)

# Import the mapping function
from scripts.setup_airtable_schema import AirtableSchemaSetup

setup = AirtableSchemaSetup(api_key, base_id)

# Test fields from Applicants
test_fields = [
    {"name": "Applicant Name", "type": "singleLineText"},
    {"name": "Email", "type": "email"},
    {"name": "Phone", "type": "phoneNumber"},
    {"name": "Location", "type": "singleLineText"},
    {"name": "Time Zone", "type": "singleSelect", "options": ["America/New_York", "America/Chicago"]},
]

# Map them using the script's function
mapped_fields = [setup.map_field_type(f) for f in test_fields]

print("Mapped fields:")
for f in mapped_fields:
    print(f"  {f}")

try:
    table = base.create_table(
        name="Test Applicants Minimal",
        fields=mapped_fields,
        description="Test"
    )
    print(f"\n✓ Success! Created table: {table.id}")
except Exception as e:
    print(f"\n✗ Error: {e}")







