from pyairtable import Api
from dotenv import load_dotenv
import os
import json

load_dotenv()
api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')

api = Api(api_key)
base = api.base(base_id)

# Try creating a table with a select field
fields = [
    {"name": "Name", "type": "singleLineText"},
    {
        "name": "Status", 
        "type": "singleSelect",
        "options": {
            "choices": [
                {"name": "Option 1"},
                {"name": "Option 2"}
            ]
        }
    }
]

print("Testing with fields:")
print(json.dumps(fields, indent=2))

try:
    table = base.create_table(
        name="Test Select",
        fields=fields
    )
    print(f"\n✓ Success! Created table: {table.id}")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()







