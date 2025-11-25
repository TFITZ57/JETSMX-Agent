from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()
api = Api(os.getenv('AIRTABLE_API_KEY'))
base = api.base(os.getenv('AIRTABLE_BASE_ID'))

# Test multilineText
try:
    table = base.create_table(
        name="Test MultilineText",
        fields=[
            {"name": "Name", "type": "singleLineText"},
            {"name": "Notes", "type": "multilineText"}
        ]
    )
    print(f"✓ Success with multilineText: {table.id}")
except Exception as e:
    print(f"✗ Failed with multilineText: {e}")

