# Airtable Agent

Central data orchestration layer for all Airtable interactions in the JetsMX Agent Framework.

## Overview

The Airtable Agent provides a unified interface for interacting with Airtable, supporting both conversational natural language queries and programmatic operations. It serves as the single source of truth for all Airtable data access across the system.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Client Applications                     │
│   (Other Agents, Services, Users)                  │
└─────────────┬──────────────────┬────────────────────┘
              │                  │
         REST API          Pub/Sub Commands
              │                  │
              v                  v
┌─────────────────────────────────────────────────────┐
│           Airtable Agent Core                        │
│  ┌───────────────┐    ┌────────────────────┐       │
│  │ Conversational│    │   Programmatic     │       │
│  │  Interface    │    │    Interface       │       │
│  │  (OpenAI LLM) │    │  (Direct calls)    │       │
│  └───────────────┘    └────────────────────┘       │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │   Query Engine │ Bulk Ops │ Analytics       │   │
│  └─────────────────────────────────────────────┘   │
└─────────────┬───────────────────────────────────────┘
              │
              v
┌─────────────────────────────────────────────────────┐
│              Airtable API                            │
└─────────────────────────────────────────────────────┘
```

## Capabilities

### 1. Conversational Interface
Ask questions in natural language:
- "How many applicants do we have?"
- "Show me all contractors with FAA A&P"
- "Export applicants to CSV"
- "Create a new applicant named John Doe"

### 2. Programmatic Operations
Direct API calls for:
- **CRUD Operations**: Create, read, update, delete records
- **Advanced Queries**: Complex filtering, sorting, searching
- **Bulk Operations**: Batch create/update/delete with validation
- **Analytics**: Count, sum, average, group-by aggregations
- **Export**: Generate CSV, JSON, or Excel files
- **Schema Introspection**: Get table and field metadata

### 3. REST API Endpoints

Base URL: `https://jetsmx-airtable-agent-[hash].run.app`

#### Core Endpoints
- `GET /health` - Health check
- `GET /airtable/tables` - List all tables
- `GET /airtable/schema` - Get schema for all tables
- `GET /airtable/schema/{table}` - Get schema for specific table

#### Query Endpoints
- `POST /airtable/query` - Natural language query
- `POST /airtable/query/advanced` - Structured query with filters

#### CRUD Endpoints
- `GET /airtable/{table}` - List records
- `GET /airtable/{table}/{record_id}` - Get single record
- `POST /airtable/{table}` - Create record
- `PUT /airtable/{table}/{record_id}` - Update record

#### Bulk Operations
- `POST /airtable/bulk/create` - Batch create records
- `POST /airtable/bulk/update` - Batch update records
- `POST /airtable/bulk/delete` - Batch delete records (requires confirmation)
- `POST /airtable/bulk/upsert` - Upsert based on key field

#### Data Operations
- `POST /airtable/export` - Export data (CSV/JSON/Excel)
- `POST /airtable/analytics` - Run analytics query

### 4. Pub/Sub Commands

Asynchronous operations via `jetsmx-airtable-commands` topic:

```python
from tools.pubsub.publisher import publish_message

publish_message(
    topic="jetsmx-airtable-commands",
    message={
        "command_id": "unique-id",
        "command_type": "export",
        "table": "Applicants",
        "format": "csv",
        "callback_url": "https://my-service.run.app/result"
    }
)
```

Supported command types:
- `query` - Query records
- `bulk_create` - Batch create
- `bulk_update` - Batch update
- `bulk_delete` - Batch delete
- `export` - Export data
- `analytics` - Run analytics

## Usage Examples

### Python (Direct Import)
```python
from agents.airtable.agent import get_airtable_agent

agent = get_airtable_agent()

# Natural language query
response = agent.ask("How many applicants are in each pipeline stage?")
print(response)

# Programmatic query
records = agent.query(
    "Applicants",
    filters=[
        {"field": "Has FAA A&P", "op": "equals", "value": True}
    ],
    max_records=10
)

# Create record
record = agent.create(
    "Applicants",
    {"Applicant Name": "John Doe", "Email": "john@example.com"},
    initiated_by="test_script",
    reason="Testing agent"
)

# Analytics
stage_counts = agent.aggregate(
    "Applicant Pipeline",
    agg_type="count",
    field="Pipeline Stage",
    group_by="Pipeline Stage"
)
```

### REST API (cURL)
```bash
# Health check
curl https://your-service.run.app/health

# Natural language query
curl -X POST https://your-service.run.app/airtable/query \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many applicants do we have?"}'

# Query with filters
curl -X POST https://your-service.run.app/airtable/query/advanced \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "table": "Applicants",
    "filters": [
      {"field": "Has FAA A&P", "op": "equals", "value": true}
    ],
    "max_records": 10
  }'

# Export to CSV
curl -X POST https://your-service.run.app/airtable/export \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "table": "Applicants",
    "format": "csv"
  }'
```

### JavaScript/TypeScript
```typescript
const API_URL = "https://your-service.run.app";
const API_KEY = "your-api-key";

// Natural language query
const response = await fetch(`${API_URL}/airtable/query`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${API_KEY}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    query: "Find all applicants with FAA A&P"
  })
});

const data = await response.json();
console.log(data.response);
```

## Deployment

### 1. Deploy REST API to Cloud Run
```bash
cd /path/to/JETSMX-AGENT-FRAMEWORK
python scripts/deploy_airtable_agent.py
```

This will:
- Build container image
- Deploy to Cloud Run
- Configure environment variables
- Output service URL

### 2. Set up Pub/Sub
```bash
python scripts/setup_airtable_command_pubsub.py
```

This creates:
- `jetsmx-airtable-commands` topic
- Pull subscription for testing
- Push subscription to pubsub handler

### 3. Test the API
```bash
# Update SERVICE_URL and API_KEY in the script
python scripts/test_airtable_agent_api.py
```

## Configuration

### Environment Variables
- `AIRTABLE_API_KEY` - Airtable API key
- `AIRTABLE_BASE_ID` - Base ID to connect to
- `OPENAI_API_KEY` - OpenAI API key for conversational interface
- `AIRTABLE_AGENT_API_KEY` - API key for REST API authentication
- `GCP_PROJECT_ID` - Google Cloud project ID

### Agent Config (`config.yaml`)
```yaml
agent:
  name: "airtable_agent"
  
capabilities:
  conversational: true
  programmatic: true
  bulk_operations: true
  export: true
  analytics: true

llm:
  provider: "openai"
  model: "gpt-4o"
  temperature: 0.1

operations:
  max_batch_size: 100
  query_timeout_seconds: 30
  export_max_records: 10000
```

## Security

### Authentication
REST API uses Bearer token authentication:
```
Authorization: Bearer YOUR_API_KEY
```

### Audit Logging
All write operations are logged with:
- Timestamp
- Initiated by (user/agent)
- Resource type and ID
- Operation details
- Reason

### Sensitive Operations
- Bulk deletes require explicit confirmation (`confirm=true`)
- Single deletes are disabled (use bulk delete instead)
- All operations are validated against schema

## Integration with Other Agents

### HR Pipeline Agent
```python
import requests

# Query applicant via REST API
response = requests.post(
    f"{AIRTABLE_AGENT_URL}/airtable/query/advanced",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "table": "Applicants",
        "filters": [
            {"field": "Email", "op": "equals", "value": "applicant@example.com"}
        ]
    }
)
applicant = response.json()["records"][0]
```

### Batch Processing Jobs
```python
from tools.pubsub.publisher import publish_message

# Request async export
publish_message(
    topic="jetsmx-airtable-commands",
    message={
        "command_id": f"export_{datetime.now().timestamp()}",
        "command_type": "export",
        "table": "Applicants",
        "format": "csv",
        "upload_to": "my-bucket/exports/applicants.csv",
        "callback_topic": "jetsmx-export-results"
    }
)
```

## Development

### Local Testing
```bash
# Install dependencies
pip install -r infra/airtable_agent/requirements.txt

# Set environment variables
export AIRTABLE_API_KEY="your-key"
export AIRTABLE_BASE_ID="your-base"
export OPENAI_API_KEY="your-key"

# Run locally
cd infra/airtable_agent
uvicorn main:app --reload --port 8080
```

### Project Structure
```
agents/airtable/
├── __init__.py
├── agent.py              # Main agent class
├── conversational.py     # Natural language interface
├── query_engine.py       # Advanced query execution
├── bulk_operations.py    # Batch processing
├── config.yaml           # Agent configuration
├── prompts.py            # LLM prompts
└── README.md             # This file

tools/airtable/
├── query_builder.py      # Programmatic query building
├── export.py             # Data export functions
├── analytics.py          # Aggregation functions
├── schema.py             # Schema introspection
└── bulk.py               # Enhanced bulk operations

infra/airtable_agent/
├── main.py               # FastAPI application
├── Dockerfile            # Container definition
├── cloudbuild.yaml       # Cloud Build config
└── requirements.txt      # Python dependencies
```

## Troubleshooting

### API Returns 401 Unauthorized
- Check `AIRTABLE_AGENT_API_KEY` is set
- Verify Authorization header format: `Bearer YOUR_KEY`

### Natural Language Queries Not Working
- Verify `OPENAI_API_KEY` is set
- Check OpenAI API quotas/limits

### Bulk Operations Timing Out
- Reduce `batch_size` parameter
- Use Pub/Sub for very large batches instead of REST API

### Schema Not Found
- Verify `schema/airtable_schema.yaml` is up to date
- Check table names match exactly (case-sensitive)

## Future Enhancements

- [ ] Rate limiting per API key
- [ ] Caching layer for frequently accessed data
- [ ] Webhook support for real-time updates
- [ ] Advanced analytics (trends, predictions)
- [ ] Multi-base support
- [ ] GraphQL interface
- [ ] Scheduled exports/reports

## Support

For questions or issues:
1. Check this README
2. Review API documentation at `/docs` endpoint
3. Check audit logs for error details
4. Contact development team

