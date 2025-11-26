from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')

api = Api(api_key)
base = api.base(base_id)

fields = [
    {"name": "Name", "type": "singleLineText"}
]

# Try with description
try:
    table = base.create_table(
        name="Test With Desc",
        fields=fields,
        description="Master record for each human applicant"
    )
    print(f"✓ Success with description! Created table: {table.id}")
except Exception as e:
    print(f"✗ Error with description: {e}")

# Try without description  
try:
    table2 = base.create_table(
        name="Test Without Desc",
        fields=fields
    )
    print(f"✓ Success without description! Created table: {table2.id}")
except Exception as e:
    print(f"✗ Error without description: {e}")







