from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()
api = Api(os.getenv('AIRTABLE_API_KEY'))
base = api.base(os.getenv('AIRTABLE_BASE_ID'))

# Test multipleSelect
try:
    table = base.create_table(
        name="Test MultiSelect",
        fields=[
            {"name": "Name", "type": "singleLineText"},
            {"name": "Tags", "type": "multipleSelect", "options": {"choices": [{"name": "A"}, {"name": "B"}]}}
        ]
    )
    print(f"✓ Success with multipleSelects: {table.id}")
except Exception as e:
    print(f"✗ Failed with multipleSelects: {e}")

