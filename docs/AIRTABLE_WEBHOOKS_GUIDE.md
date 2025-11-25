# Airtable Webhooks API Integration Guide

## Overview

This system uses **Airtable's Webhooks API** to programmatically subscribe to table changes and trigger custom workflows. Instead of relying on Airtable's built-in automations, we run our own workflow engine with per-table handlers.

## Architecture

```
Airtable Base Changes
    ↓
Airtable Webhooks API
    ↓
Cloud Run (jetsmx-webhooks)
    ↓ 
HMAC Signature Verification
    ↓
Custom Table Handlers
    ↓
Pub/Sub → Agent Processing
```

## Components

### 1. Webhook API Client (`tools/airtable/webhooks.py`)

Python client for Airtable's Webhooks API:

```python
from tools.airtable.webhooks import get_webhook_client

client = get_webhook_client()

# Create webhook
webhook = client.create_webhook(
    base_id="appXXXXXXXXXXXXXX",
    notification_url="https://your-app.run.app/webhooks/airtable"
)

# Enable notifications
client.enable_notifications(base_id, webhook['id'])

# List webhooks
webhooks = client.list_webhooks(base_id)

# Refresh webhook (extends expiration)
client.refresh_webhook(base_id, webhook_id)

# Delete webhook
client.delete_webhook(base_id, webhook_id)
```

### 2. Signature Verification (`infra/webhooks/middleware.py`)

Automatically verifies HMAC-SHA256 signatures on incoming webhooks:

- Checks `X-Airtable-Content-MAC` header
- Uses `AIRTABLE_WEBHOOK_SECRET` from environment
- Rejects invalid/missing signatures
- Skips verification in dev mode if secret not configured

### 3. Custom Handlers (`infra/webhooks/handlers/`)

Per-table handlers process events:

- **`ApplicantPipelineHandler`** - Pipeline stage transitions, screening approvals
- **`ApplicantsHandler`** - Profile updates, data enrichment
- **`InteractionsHandler`** - Audit log tracking
- **`ContractorsHandler`** - Contractor lifecycle events

Each handler:
- Receives Airtable webhook payload
- Extracts changed fields and values
- Applies business logic
- Publishes to Pub/Sub for async agent processing

### 4. Webhook Router (`infra/webhooks/routes/airtable.py`)

Main endpoint: `POST /webhooks/airtable`

Receives Airtable payloads:
```json
{
  "baseId": "appXXX",
  "webhookId": "achXXX",
  "timestamp": "2025-11-25T...",
  "baseTransactionNumber": 123,
  "changedTablesById": {
    "tblXXX": {
      "name": "applicant_pipeline",
      "changedRecordsById": {
        "recXXX": {
          "current": {
            "id": "recXXX",
            "cellValuesByFieldId": {...}
          },
          "previous": {
            "cellValuesByFieldId": {...}
          }
        }
      },
      "createdRecordsById": {...},
      "destroyedRecordIds": [...]
    }
  }
}
```

Routes to appropriate handler based on table name.

### 5. Auto-Sync Script (`scripts/sync_airtable_webhooks.py`)

Reads `SCHEMA/event_routing.yaml` and auto-creates webhooks:

```bash
# Dry run (preview changes)
python scripts/sync_airtable_webhooks.py --dry-run

# Create webhooks
python scripts/sync_airtable_webhooks.py

# Force recreate (deletes existing)
python scripts/sync_airtable_webhooks.py --force
```

Features:
- Idempotent - safe to run multiple times
- Auto-detects tables from routing rules
- Creates base-wide webhook (watches all tables)
- Enables notifications automatically
- Outputs MAC secret for `.env`

## Setup Instructions

### Step 1: Configure Environment

Add to `.env`:

```bash
# Airtable Webhook Configuration
AIRTABLE_API_KEY=patXXXXXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
AIRTABLE_WEBHOOK_SECRET=  # Set after running sync script

# Cloud Run
WEBHOOK_BASE_URL=https://jetsmx-webhooks-xxxxx.run.app
```

### Step 2: Deploy Cloud Run Services

Webhooks need a live endpoint to receive notifications:

```bash
# Deploy webhook receiver
./scripts/deploy_cloud_run.sh

# Get the webhook URL
gcloud run services describe jetsmx-webhooks \
  --region us-central1 \
  --format='value(status.url)'
```

Add the URL to `.env` as `WEBHOOK_BASE_URL`.

### Step 3: Create Webhook Subscriptions

```bash
python scripts/sync_airtable_webhooks.py
```

This will:
1. Read `SCHEMA/event_routing.yaml`
2. Extract tables that need monitoring
3. Create webhook subscription
4. Enable notifications
5. Print MAC secret

**IMPORTANT**: Copy the MAC secret to `.env`:

```bash
AIRTABLE_WEBHOOK_SECRET=abc123def456...
```

### Step 4: Verify Setup

Test the webhook:

```bash
# Check webhook status
python -c "
from tools.airtable.webhooks import get_webhook_client
from shared.config.settings import get_settings

client = get_webhook_client()
settings = get_settings()
webhooks = client.list_webhooks(settings.airtable_base_id)

for w in webhooks:
    print(f'{w[\"id\"]}: {w[\"isHookEnabled\"]}, expires {w[\"expirationTime\"]}')
"

# Make a change in Airtable and check logs
# Cloud Run logs should show webhook received and processed
```

## Webhook Lifecycle

### Expiration

Webhooks expire after **7 days of no activity**. Refresh them regularly:

```bash
# Manual refresh
python scripts/refresh_airtable_webhooks.py

# Or set up a cron/Cloud Scheduler job to run every 6 days
```

### Automated Refresh (Optional)

Add to Cloud Scheduler:

```bash
gcloud scheduler jobs create http refresh-airtable-webhooks \
  --schedule="0 0 */6 * *" \
  --uri="https://jetsmx-webhooks-xxxxx.run.app/internal/scheduler/refresh-webhooks" \
  --http-method=POST \
  --oidc-service-account-email=jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com
```

Then implement the endpoint in `infra/webhooks/routes/scheduler.py`.

## Adding New Tables

1. **Update Schema**: Add table to `SCHEMA/airtable_schema.yaml`

2. **Update Routing**: Add routing rules to `SCHEMA/event_routing.yaml`:

```yaml
events:
  - name: "new_table_event"
    source: "airtable"
    routing_rules:
      - condition: |
          table_id == "new_table"
          and "Status" in changed_fields
        action:
          graph: "some_graph"
          entry_node: "some_node"
```

3. **Create Handler**: Add handler in `infra/webhooks/handlers/new_table_handler.py`:

```python
from infra.webhooks.handlers.base_handler import BaseWebhookHandler

class NewTableHandler(BaseWebhookHandler):
    async def handle(self, payload):
        # Process webhook
        pass
```

4. **Register Handler**: Update `infra/webhooks/routes/airtable.py`:

```python
from infra.webhooks.handlers.new_table_handler import NewTableHandler

HANDLERS = {
    # ... existing handlers
    "new_table": NewTableHandler(),
}
```

5. **Re-sync**: Webhook already watches all tables, no need to recreate!

## Monitoring & Debugging

### View Recent Webhook Payloads

```python
from tools.airtable.webhooks import get_webhook_client
from shared.config.settings import get_settings

client = get_webhook_client()
settings = get_settings()

webhooks = client.list_webhooks(settings.airtable_base_id)
webhook_id = webhooks[0]['id']

# Get last 10 payloads
payloads = client.list_webhook_payloads(
    settings.airtable_base_id,
    webhook_id,
    limit=10
)

for p in payloads['payloads']:
    print(f"Timestamp: {p['timestamp']}")
    print(f"Tables: {list(p.get('changedTablesById', {}).keys())}")
```

### Check Cloud Run Logs

```bash
# View webhook receiver logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=jetsmx-webhooks" \
  --limit 50 \
  --format json
```

### Test Webhook Locally

```bash
# Start local server
cd /Users/TFitz/JETSMX-AGENT-FRAMEWORK
uvicorn infra.webhooks.main:app --reload --port 8080

# Create test webhook pointing to ngrok/localtunnel
ngrok http 8080
# Then update webhook notification URL to ngrok URL
```

## Security

1. **Signature Verification**: Always enabled in production
2. **HTTPS Only**: Cloud Run enforces TLS
3. **Secret Rotation**: Rotate MAC secret if compromised:
   ```bash
   python scripts/sync_airtable_webhooks.py --force
   ```
4. **Minimal Permissions**: Service account only needs Pub/Sub publish

## Troubleshooting

### Webhook Not Receiving Events

1. Check webhook is enabled:
   ```python
   webhooks = client.list_webhooks(base_id)
   print(webhooks[0]['isHookEnabled'])  # Should be True
   ```

2. Check webhook hasn't expired:
   ```python
   print(webhooks[0]['expirationTime'])
   ```

3. Verify notification URL is correct:
   ```python
   print(webhooks[0]['notificationUrl'])
   ```

4. Check Cloud Run logs for 4xx/5xx errors

### Signature Verification Failing

1. Verify `AIRTABLE_WEBHOOK_SECRET` matches webhook MAC secret
2. Check middleware isn't modifying request body before verification
3. Ensure header name is exactly `X-Airtable-Content-MAC`

### Handler Not Triggering

1. Check table name mapping in `HANDLERS` dict
2. Verify `changedTablesById` contains expected table
3. Check handler logs for exceptions
4. Ensure Pub/Sub topic exists and is accessible

## Performance

- Webhooks are near real-time (< 1 second latency)
- Handlers process async via Pub/Sub
- No polling overhead
- Scales automatically with Cloud Run

## Comparison to Airtable Automations

| Feature | Airtable Automations | Our Webhooks API |
|---------|---------------------|------------------|
| Setup | GUI-based | Code-based |
| Logic | Limited conditions | Full Python |
| Integrations | Pre-built only | Any API/service |
| Cost | Usage-based | Free (except Cloud Run) |
| Version Control | No | Yes (git) |
| Testing | Manual | Automated |
| Debugging | Limited | Full logs |
| Scalability | Automation limits | Unlimited |

## References

- [Airtable Webhooks API Docs](https://airtable.com/developers/web/api/webhooks-overview)
- [Webhook Specification](https://airtable.com/developers/web/api/model/webhooks-specification)
- [Webhook Payloads](https://airtable.com/developers/web/api/model/webhooks-payload)

