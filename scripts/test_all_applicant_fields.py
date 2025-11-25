from pyairtable import Api
from dotenv import load_dotenv
import os
import json

load_dotenv()
api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')

api = Api(api_key)
base = api.base(base_id)

# All 21 basic fields from Applicants table
fields = [
    {'name': 'Applicant Name', 'type': 'singleLineText'},
    {'name': 'Email', 'type': 'email'},
    {'name': 'Phone', 'type': 'phoneNumber'},
    {'name': 'Location', 'type': 'singleLineText'},
    {'name': 'Time Zone', 'type': 'singleSelect', 'options': {'choices': [{'name': 'America/New_York'}, {'name': 'America/Chicago'}, {'name': 'America/Denver'}, {'name': 'America/Los_Angeles'}, {'name': 'Other'}]}},
    {'name': 'Resume Drive File ID', 'type': 'singleLineText'},
    {'name': 'Resume Link', 'type': 'url'},
    {'name': 'ICC PDF Drive File ID', 'type': 'singleLineText'},
    {'name': 'ICC PDF Link', 'type': 'url'},
    {'name': 'Has FAA A&P', 'type': 'checkbox', 'options': {}},
    {'name': 'FAA A&P #', 'type': 'singleLineText'},
    {'name': 'Other Certs', 'type': 'longText'},
    {'name': 'Years in Aviation', 'type': 'number', 'options': {'precision': 0}},
    {'name': 'Business Aviation Experience', 'type': 'checkbox', 'options': {}},
    {'name': 'AOG / Field Experience', 'type': 'checkbox', 'options': {}},
    {'name': 'Geographic Flexibility', 'type': 'singleSelect', 'options': {'choices': [{'name': 'Local-only'}, {'name': 'NE Corridor'}, {'name': 'US-wide'}]}},
    {'name': 'On-call AOG Suitability Score', 'type': 'number', 'options': {'precision': 0}},
    {'name': 'Baseline Verdict', 'type': 'singleSelect', 'options': {'choices': [{'name': 'Strong Fit'}, {'name': 'Maybe'}, {'name': 'Not a Fit'}, {'name': 'Needs More Info'}]}},
    {'name': 'Missing Info Summary', 'type': 'longText'},
    {'name': 'Follow-up Questions', 'type': 'longText'},
    {'name': 'Source', 'type': 'singleSelect', 'options': {'choices': [{'name': 'Drive Resume'}, {'name': 'Referral'}, {'name': 'Job Board'}, {'name': 'Website'}, {'name': 'Other'}]}}
]

print(f"Testing with {len(fields)} fields")

try:
    table = base.create_table(
        name="Test All Applicant Fields",
        fields=fields,
        description="Master record for each human applicant"
    )
    print(f"\n✓ Success! Created table: {table.id}")
except Exception as e:
    print(f"\n✗ Error: {e}")
    
    # Try with first 10 fields
    print("\nTrying with first 10 fields...")
    try:
        table2 = base.create_table(
            name="Test First 10",
            fields=fields[:10]
        )
        print(f"✓ Success with first 10! Created table: {table2.id}")
    except Exception as e2:
        print(f"✗ Error with first 10: {e2}")

