from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')

api = Api(api_key)
base = api.base(base_id)

# Try creating a simple test table
try:
    table = base.create_table(
        name="Test Simple",
        fields=[
            {"name": "Name", "type": "singleLineText"}
        ]
    )
    print(f"Success! Created table: {table.id}")
    print(f"Fields: {[f.name for f in table.fields]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()







