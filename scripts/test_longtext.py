from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()
api = Api(os.getenv('AIRTABLE_API_KEY'))
base = api.base(os.getenv('AIRTABLE_BASE_ID'))

# Test longText without options
try:
    table = base.create_table(
        name="Test LongText No Opt",
        fields=[
            {"name": "Name", "type": "singleLineText"},
            {"name": "Notes", "type": "longText"}
        ]
    )
    print(f"✓ Success without options: {table.id}")
except Exception as e:
    print(f"✗ Failed without options: {e}")

# Test longText with empty options  
try:
    table2 = base.create_table(
        name="Test LongText With Opt",
        fields=[
            {"name": "Name", "type": "singleLineText"},
            {"name": "Notes", "type": "longText", "options": {}}
        ]
    )
    print(f"✓ Success with empty options: {table2.id}")
except Exception as e:
    print(f"✗ Failed with empty options: {e}")







