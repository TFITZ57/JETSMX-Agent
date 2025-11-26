# Airtable Agent Integration Guide

## Overview

The Airtable Agent is now the **central data orchestration layer** for all Airtable interactions in the JetsMX Agent Framework. This document explains how it integrates with existing components and how to migrate to using it.

## What Was Built

### 1. Agent Core (`agents/airtable/`)
- **Conversational Interface**: Natural language queries via OpenAI
- **Programmatic Interface**: Direct Python API
- **Query Engine**: Advanced filtering, joins, aggregations
- **Bulk Operations**: Batch create/update/delete with validation
- **Export Engine**: CSV, JSON, Excel generation
- **Analytics**: Count, sum, average, group-by operations

### 2. REST API Service (`infra/airtable_agent/`)
- FastAPI application with comprehensive endpoints
- Deployed to Cloud Run as `jetsmx-airtable-agent`
- Bearer token authentication
- Full OpenAPI documentation at `/docs`

### 3. Pub/Sub Integration
- New topic: `jetsmx-airtable-commands`
- Async command handler in `infra/pubsub_handlers/handlers/airtable_commands_handler.py`
- Router updated to handle airtable-commands events
- Support for long-running operations (exports, bulk ops)

### 4. Enhanced Tools Layer (`tools/airtable/`)
- `query_builder.py` - Programmatic formula builder
- `export.py` - Multi-format export functions
- `analytics.py` - Aggregation and reporting
- `schema.py` - Schema introspection and validation
- `bulk.py` - Enhanced batch operations

### 5. Models & Types (`shared/models/`)
- `airtable_requests.py` - REST API request models
- `airtable_responses.py` - REST API response models
- `airtable_commands.py` - Pub/Sub command models

## Integration Patterns

### Pattern 1: Direct Import (Same Process)

**Use when**: Agent code runs in the same process as Airtable Agent

```python
from agents.airtable.agent import get_airtable_agent

agent = get_airtable_agent()

# Natural language
response = agent.ask("How many applicants do we have?")

# Programmatic
records = agent.query("Applicants", max_records=10)
applicant = agent.create("Applicants", {"Applicant Name": "John"})
```

**Best for**:
- HR Pipeline Agent
- Applicant Analysis Agent
- Company KB Agent

### Pattern 2: REST API (Cross-Service)

**Use when**: Calling from external services, web apps, or different processes

```python
import requests

AIRTABLE_AGENT_URL = "https://jetsmx-airtable-agent-xyz.run.app"
API_KEY = os.getenv("AIRTABLE_AGENT_API_KEY")

headers = {"Authorization": f"Bearer {API_KEY}"}

# Query applicants
response = requests.post(
    f"{AIRTABLE_AGENT_URL}/airtable/query/advanced",
    headers=headers,
    json={
        "table": "Applicants",
        "filters": [{"field": "Email", "op": "equals", "value": email}],
        "max_records": 1
    }
)
applicant = response.json()["records"][0]

# Create record
response = requests.post(
    f"{AIRTABLE_AGENT_URL}/airtable/Applicants",
    headers=headers,
    json={
        "fields": {"Applicant Name": "Jane", "Email": "jane@example.com"},
        "initiated_by": "external_service",
        "reason": "New applicant registration"
    }
)
```

**Best for**:
- External web applications
- Third-party integrations
- Microservices architecture
- JavaScript/frontend apps

### Pattern 3: Pub/Sub Commands (Async)

**Use when**: Long-running operations, batch jobs, or fire-and-forget

```python
from tools.pubsub.publisher import publish_message

# Bulk export
publish_message(
    topic="jetsmx-airtable-commands",
    message={
        "command_id": "export_123",
        "command_type": "export",
        "table": "Applicants",
        "format": "csv",
        "filters": [{"field": "Pipeline Stage", "op": "equals", "value": "Active"}],
        "upload_to": "jetsmx-exports/applicants_active.csv",
        "callback_url": "https://my-service.run.app/export-complete"
    }
)

# Bulk create (thousands of records)
publish_message(
    topic="jetsmx-airtable-commands",
    message={
        "command_id": "bulk_import_123",
        "command_type": "bulk_create",
        "table": "Interactions",
        "records": large_list_of_records,
        "batch_size": 50,
        "callback_topic": "jetsmx-import-results"
    }
)
```

**Best for**:
- Batch processing jobs
- Scheduled exports
- Data imports
- Any operation with >100 records

## Migration Guide

### Step 1: Identify Current Airtable Usage

Search codebase for direct Airtable tool usage:
```bash
grep -r "from tools.airtable" --include="*.py"
grep -r "airtable_create_" --include="*.py"
grep -r "airtable_update_" --include="*.py"
```

### Step 2: Choose Integration Pattern

| Current Code | Recommended Pattern | Why |
|--------------|-------------------|-----|
| Agent internal code | Direct Import | Same process, fast, typed |
| Webhook handlers | Direct Import or REST | Depends on deployment |
| External services | REST API | Language agnostic, secure |
| Batch jobs | Pub/Sub | Async, scalable, resumable |
| Frontend apps | REST API | Standard HTTP interface |

### Step 3: Update Code

**Before (Direct Airtable Tools)**:
```python
from tools.airtable_tools import find_records, create_record

# Old way
records = find_records(
    settings.airtable_base_id,
    "Applicants",
    formula="{Email} = 'test@example.com'"
)
```

**After (Airtable Agent)**:
```python
from agents.airtable.agent import get_airtable_agent

agent = get_airtable_agent()

# New way - cleaner, validated
records = agent.find_by_email("Applicants", "test@example.com")

# Or with natural language
response = agent.ask("Find applicant with email test@example.com")
```

### Step 4: Update Existing Agents

#### HR Pipeline Agent
```python
# In agents/hr_pipeline/agent.py

from agents.airtable.agent import get_airtable_agent

class HRPipelineAgent:
    def __init__(self):
        self.airtable = get_airtable_agent()  # Add this
    
    def generate_outreach_draft(self, pipeline_id: str):
        # Old: get_pipeline_record(pipeline_id)
        # New:
        pipeline = self.airtable.get("Applicant Pipeline", pipeline_id)
```

#### Company KB Agent
```python
# Can now delegate to Airtable Agent for natural language queries

def query(self, question: str):
    # If question is about Airtable data:
    if self._is_airtable_question(question):
        airtable_agent = get_airtable_agent()
        return airtable_agent.ask(question)
```

## Example Use Cases

### Use Case 1: User Dashboard Query

**Frontend** → **REST API** → **Airtable Agent**

```javascript
// React component
async function fetchApplicantStats() {
  const response = await fetch(
    `${AIRTABLE_AGENT_URL}/airtable/analytics`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        table: 'Applicant Pipeline',
        agg_type: 'count',
        field: 'Pipeline Stage',
        group_by: 'Pipeline Stage'
      })
    }
  );
  
  const data = await response.json();
  return data.result; // { "New": 10, "Screening": 5, ... }
}
```

### Use Case 2: Nightly Export Job

**Cloud Scheduler** → **Pub/Sub** → **Airtable Agent** → **Cloud Storage**

```python
# Scheduled function
def export_daily_report():
    publish_message(
        topic="jetsmx-airtable-commands",
        message={
            "command_id": f"daily_export_{date.today()}",
            "command_type": "export",
            "table": "Applicants",
            "format": "excel",
            "filters": [
                {"field": "Created At", "op": "date_is_same", "value": "today"}
            ],
            "upload_to": f"reports/applicants_{date.today()}.xlsx"
        }
    )
```

### Use Case 3: Bulk Data Import

**Admin Script** → **Pub/Sub** → **Airtable Agent**

```python
# scripts/import_applicants.py
import csv

with open('applicants.csv', 'r') as f:
    reader = csv.DictReader(f)
    records = [{"fields": row} for row in reader]

# Split into chunks of 100
for i in range(0, len(records), 100):
    chunk = records[i:i+100]
    
    publish_message(
        topic="jetsmx-airtable-commands",
        message={
            "command_id": f"import_chunk_{i}",
            "command_type": "bulk_create",
            "table": "Applicants",
            "records": chunk,
            "validate": True,
            "callback_topic": "import-results"
        }
    )
```

### Use Case 4: Chat Bot Query

**Google Chat** → **Chat Handler** → **Airtable Agent**

```python
# In chat handler
def handle_chat_message(message_text: str):
    airtable_agent = get_airtable_agent()
    
    # Natural language query
    response = airtable_agent.ask(message_text)
    
    # Post response back to Chat
    post_message(chat_space_id, response)
```

## Deployment Checklist

- [ ] Deploy Airtable Agent REST API:
  ```bash
  python scripts/deploy_airtable_agent.py
  ```

- [ ] Set up Pub/Sub infrastructure:
  ```bash
  python scripts/setup_airtable_command_pubsub.py
  ```

- [ ] Set required secrets in Secret Manager:
  - `AIRTABLE_API_KEY`
  - `AIRTABLE_BASE_ID`
  - `OPENAI_API_KEY`
  - `AIRTABLE_AGENT_API_KEY` (for REST API auth)

- [ ] Test REST API:
  ```bash
  python scripts/test_airtable_agent_api.py <SERVICE_URL> <API_KEY>
  ```

- [ ] Update environment variables in other services to include:
  ```
  AIRTABLE_AGENT_URL=https://jetsmx-airtable-agent-xyz.run.app
  AIRTABLE_AGENT_API_KEY=your-key
  ```

- [ ] Migrate existing code (see Migration Guide above)

- [ ] Update monitoring/alerting to include new service

## Benefits

### Before (Direct Airtable Tools)
- Scattered Airtable logic across multiple files
- No validation or error handling consistency
- No audit trail
- No natural language interface
- Limited analytics capabilities
- Manual formula building

### After (Airtable Agent)
- ✅ Single source of truth
- ✅ Consistent validation and error handling
- ✅ Comprehensive audit logging
- ✅ Natural language queries
- ✅ Advanced analytics and reporting
- ✅ Programmatic query building
- ✅ Multiple access patterns (direct, REST, Pub/Sub)
- ✅ Schema-aware operations
- ✅ Bulk operations with rollback
- ✅ Multi-format exports

## Monitoring

### Health Checks
```bash
# REST API health
curl https://jetsmx-airtable-agent-xyz.run.app/health

# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=jetsmx-airtable-agent" --limit 50
```

### Metrics to Monitor
- API request rate and latency
- Error rates by endpoint
- Bulk operation success rates
- Pub/Sub message processing time
- Airtable API quota usage

### Alerts to Set Up
- REST API down (health check fails)
- High error rate (>5% of requests)
- Slow queries (>10s response time)
- Pub/Sub message backlog (>100 pending)
- Airtable API rate limiting

## Troubleshooting

### "401 Unauthorized" errors
→ Check `AIRTABLE_AGENT_API_KEY` is set and correct in client

### Natural language queries not working
→ Verify `OPENAI_API_KEY` is set in Cloud Run service

### Bulk operations timing out
→ Use Pub/Sub instead of REST API for large batches

### Schema validation errors
→ Update `schema/airtable_schema.yaml` to match current Airtable base

### Pub/Sub messages not processing
→ Check pubsub handler is deployed and subscription is active

## Next Steps

1. **Deploy** the Airtable Agent (follow Deployment Checklist)
2. **Test** with the provided test script
3. **Migrate** one agent at a time (start with Company KB)
4. **Monitor** performance and errors
5. **Iterate** based on usage patterns

## Resources

- Agent README: `agents/airtable/README.md`
- API Documentation: `https://your-service.run.app/docs`
- Example Scripts: `scripts/test_airtable_agent_api.py`
- Deployment Scripts: `scripts/deploy_airtable_agent.py`

