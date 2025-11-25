from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()
api = Api(os.getenv('AIRTABLE_API_KEY'))
base = api.base(os.getenv('AIRTABLE_BASE_ID'))

# Test multipleSelects (plural)
try:
    table = base.create_table(
        name="Test MultipleSelects",
        fields=[
            {"name": "Name", "type": "singleLineText"},
            {"name": "Tags", "type": "multipleSelects", "options": {"choices": [{"name": "A"}, {"name": "B"}]}}
        ]
    )
    print(f"✓ Success with multipleSelects (plural): {table.id}")
except Exception as e:
    print(f"✗ Failed with multipleSelects (plural): {e}")

