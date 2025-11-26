#!/usr/bin/env python3
"""
Test script for Airtable Agent REST API.
"""
import requests
import json
from shared.config.settings import get_settings

settings = get_settings()

# Get service URL from environment or use local
SERVICE_URL = "http://localhost:8080"  # Change to your deployed URL
API_KEY = "test-key"  # Set your API key

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def test_health():
    """Test health endpoint."""
    print("\n🏥 Testing health endpoint...")
    response = requests.get(f"{SERVICE_URL}/health")
    
    if response.status_code == 200:
        print("✓ Health check passed!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Health check failed: {response.status_code}")
        print(response.text)


def test_list_tables():
    """Test list tables endpoint."""
    print("\n📋 Testing list tables...")
    response = requests.get(
        f"{SERVICE_URL}/airtable/tables",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✓ List tables successful!")
        data = response.json()
        print(f"Found {len(data.get('tables', []))} tables:")
        for table in data.get('tables', []):
            print(f"  - {table}")
    else:
        print(f"❌ List tables failed: {response.status_code}")
        print(response.text)


def test_get_schema():
    """Test get schema endpoint."""
    print("\n📊 Testing get schema for Applicants table...")
    response = requests.get(
        f"{SERVICE_URL}/airtable/schema/Applicants",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✓ Get schema successful!")
        data = response.json()
        schema = data.get('schema', {})
        print(f"Table: {schema.get('name')}")
        print(f"Fields: {schema.get('field_count')}")
    else:
        print(f"❌ Get schema failed: {response.status_code}")
        print(response.text)


def test_query_records():
    """Test query records endpoint."""
    print("\n🔍 Testing query Applicants (limit 5)...")
    response = requests.get(
        f"{SERVICE_URL}/airtable/Applicants?max_records=5",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✓ Query successful!")
        data = response.json()
        print(f"Found {data.get('count')} records")
    else:
        print(f"❌ Query failed: {response.status_code}")
        print(response.text)


def test_natural_language_query():
    """Test natural language query endpoint."""
    print("\n💬 Testing natural language query...")
    response = requests.post(
        f"{SERVICE_URL}/airtable/query",
        headers=headers,
        json={
            "query": "How many applicants do we have?"
        }
    )
    
    if response.status_code == 200:
        print("✓ Natural language query successful!")
        data = response.json()
        print(f"Response: {data.get('response')}")
    else:
        print(f"❌ Natural language query failed: {response.status_code}")
        print(response.text)


def test_advanced_query():
    """Test advanced query with filters."""
    print("\n🔎 Testing advanced query with filters...")
    response = requests.post(
        f"{SERVICE_URL}/airtable/query/advanced",
        headers=headers,
        json={
            "table": "Applicants",
            "filters": [
                {"field": "Has FAA A&P", "op": "equals", "value": True}
            ],
            "max_records": 10
        }
    )
    
    if response.status_code == 200:
        print("✓ Advanced query successful!")
        data = response.json()
        print(f"Found {data.get('count')} applicants with FAA A&P")
    else:
        print(f"❌ Advanced query failed: {response.status_code}")
        print(response.text)


def test_analytics():
    """Test analytics endpoint."""
    print("\n📊 Testing analytics (count by pipeline stage)...")
    response = requests.post(
        f"{SERVICE_URL}/airtable/analytics",
        headers=headers,
        json={
            "table": "Applicant Pipeline",
            "agg_type": "count",
            "field": "Pipeline Stage",
            "group_by": "Pipeline Stage"
        }
    )
    
    if response.status_code == 200:
        print("✓ Analytics successful!")
        data = response.json()
        result = data.get('result', {})
        print("Pipeline stage counts:")
        for stage, count in result.items():
            print(f"  {stage}: {count}")
    else:
        print(f"❌ Analytics failed: {response.status_code}")
        print(response.text)


def run_all_tests():
    """Run all test functions."""
    print("🧪 Testing Airtable Agent REST API")
    print(f"📍 Service URL: {SERVICE_URL}")
    print("=" * 60)
    
    try:
        test_health()
        test_list_tables()
        test_get_schema()
        test_query_records()
        test_natural_language_query()
        test_advanced_query()
        test_analytics()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to {SERVICE_URL}")
        print("Make sure the service is running locally or update SERVICE_URL")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        SERVICE_URL = sys.argv[1]
    if len(sys.argv) > 2:
        API_KEY = sys.argv[2]
    
    run_all_tests()

