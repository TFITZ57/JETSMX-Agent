from pyairtable import Api
from dotenv import load_dotenv
import os
import json

load_dotenv()
api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')

api = Api(api_key)
base = api.base(base_id)

# Try creating a table with time fields
fields = [
    {"name": "Name", "type": "singleLineText"},
    {"name": "Created At", "type": "createdTime"},
    {"name": "Last Updated", "type": "lastModifiedTime"}
]

print("Testing with fields:")
print(json.dumps(fields, indent=2))

try:
    table = base.create_table(
        name="Test Time Fields",
        fields=fields
    )
    print(f"\n✓ Success! Created table: {table.id}")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

