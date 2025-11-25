from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')

api = Api(api_key)
base = api.base(base_id)

fields = [
    {"name": "Name", "type": "singleLineText"},
    {"name": "Active", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}}
]

try:
    table = base.create_table(
        name="Test Checkbox Final",
        fields=fields
    )
    print(f"✓ Success! Created table: {table.id}")
except Exception as e:
    print(f"✗ Error: {e}")

