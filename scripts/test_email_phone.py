from pyairtable import Api
from dotenv import load_dotenv
import os
import json

load_dotenv()
api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')

api = Api(api_key)
base = api.base(base_id)

# Test with email and phone
fields = [
    {"name": "Applicant Name", "type": "singleLineText"},
    {"name": "Email", "type": "email"},
    {"name": "Phone", "type": "phoneNumber"},
    {"name": "Resume Link", "type": "url"}
]

print("Testing with fields:")
print(json.dumps(fields, indent=2))

try:
    table = base.create_table(
        name="Test Email Phone",
        fields=fields
    )
    print(f"\n✓ Success! Created table: {table.id}")
except Exception as e:
    print(f"\n✗ Error: {e}")

