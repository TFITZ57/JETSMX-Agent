# Airtable Webhooks API Integration - Implementation Summary

## ✅ What Was Implemented

### 1. Webhook API Client (`tools/airtable/webhooks.py`)
Full-featured Python client for Airtable's Webhooks API:
- ✅ `create_webhook()` - Create webhook subscriptions
- ✅ `list_webhooks()` - List active webhooks
- ✅ `get_webhook()` - Get webhook details
- ✅ `delete_webhook()` - Remove subscriptions
- ✅ `enable_notifications()` - Enable webhook
- ✅ `refresh_webhook()` - Extend expiration time
- ✅ `list_webhook_payloads()` - Debug recent payloads
- ✅ `verify_webhook_signature()` - HMAC-SHA256 validation

### 2. Signature Verification Middleware (`infra/webhooks/middleware.py`)
- ✅ HMAC-SHA256 signature verification
- ✅ `X-Airtable-Content-MAC` header validation
- ✅ Automatic rejection of invalid signatures
- ✅ Dev mode support (skips verification if secret not set)

### 3. Custom Handler Framework (`infra/webhooks/handlers/`)
Base handler class with utilities:
- ✅ `BaseWebhookHandler` - Abstract base with common utilities
  - Field diffing (`extract_changed_fields()`)
  - Value extraction (`get_field_value()`, `get_field_changes()`)
  - Condition checking (`check_condition()`)
  - Structured logging

Per-table handlers:
- ✅ `ApplicantPipelineHandler` - Pipeline transitions, screening, background checks
- ✅ `ApplicantsHandler` - Profile updates, data enrichment
- ✅ `InteractionsHandler` - Audit log processing
- ✅ `ContractorsHandler` - Contractor lifecycle events

### 4. Enhanced Webhook Router (`infra/webhooks/routes/airtable.py`)
- ✅ Universal webhook endpoint (`POST /webhooks/airtable`)
- ✅ Airtable payload parsing (`changedTablesById`, `createdRecordsById`)
- ✅ Dynamic handler dispatch based on table name
- ✅ Multi-table event processing
- ✅ Legacy endpoint support for backwards compatibility

### 5. Auto-Sync Script (`scripts/sync_airtable_webhooks.py`)
- ✅ Reads `SCHEMA/event_routing.yaml`
- ✅ Auto-detects tables needing webhooks
- ✅ Idempotent - safe to run multiple times
- ✅ Dry-run mode (`--dry-run`)
- ✅ Force recreate mode (`--force`)
- ✅ Auto-enables notifications
- ✅ Outputs MAC secret for `.env`

### 6. Webhook Refresh Script (`scripts/refresh_airtable_webhooks.py`)
- ✅ Refreshes all webhooks in base
- ✅ Extends expiration time (7 days)
- ✅ Shows old/new expiration times

### 7. Configuration Updates
- ✅ Added `airtable_webhook_secret` to `Settings`
- ✅ Added `webhook_base_url` to `Settings`
- ✅ Updated `env.template` with new variables
- ✅ Added comments and documentation

### 8. Documentation
- ✅ `docs/AIRTABLE_WEBHOOKS_GUIDE.md` - Complete usage guide
- ✅ Updated `NEXT_STEPS.md` with webhook setup
- ✅ Inline code documentation and docstrings

## 📁 Files Created

**New Files:**
```
tools/airtable/webhooks.py                              (364 lines)
infra/webhooks/handlers/__init__.py                     (17 lines)
infra/webhooks/handlers/base_handler.py                 (173 lines)
infra/webhooks/handlers/applicant_pipeline_handler.py   (158 lines)
infra/webhooks/handlers/applicants_handler.py           (101 lines)
infra/webhooks/handlers/interactions_handler.py         (77 lines)
infra/webhooks/handlers/contractors_handler.py          (121 lines)
scripts/sync_airtable_webhooks.py                       (346 lines)
scripts/refresh_airtable_webhooks.py                    (89 lines)
docs/AIRTABLE_WEBHOOKS_GUIDE.md                         (442 lines)
docs/IMPLEMENTATION_AIRTABLE_WEBHOOKS.md                (this file)
```

**Modified Files:**
```
infra/webhooks/middleware.py                            (+ signature verification)
infra/webhooks/routes/airtable.py                       (complete rewrite)
shared/config/settings.py                               (+ webhook settings)
env.template                                            (+ webhook vars)
NEXT_STEPS.md                                           (+ webhook setup)
```

## 🔧 How It Works

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User changes record in Airtable                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Airtable Webhooks API sends POST to notification URL     │
│    Payload: {baseId, webhookId, changedTablesById, ...}    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Cloud Run receives webhook at /webhooks/airtable         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Middleware verifies HMAC signature                        │
│    X-Airtable-Content-MAC vs computed HMAC                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Router extracts changed tables and dispatches            │
│    table_name → HANDLERS[table_name]                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Handler processes event (ApplicantPipelineHandler, etc)  │
│    - Extracts changed fields                                │
│    - Applies business logic                                 │
│    - Publishes to Pub/Sub                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Pub/Sub delivers to agent processors                     │
│    Agents execute workflows based on event_routing.yaml     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Setup Instructions

### Prerequisites
1. Cloud Run services deployed
2. `WEBHOOK_BASE_URL` in `.env`
3. `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID` in `.env`

### Quick Start

```bash
# 1. Preview webhook creation
python scripts/sync_airtable_webhooks.py --dry-run

# 2. Create webhooks
python scripts/sync_airtable_webhooks.py

# 3. Copy MAC secret from output to .env
echo "AIRTABLE_WEBHOOK_SECRET=abc123..." >> .env

# 4. Test webhook
# Make a change in Airtable and check Cloud Run logs

# 5. Set up periodic refresh (optional)
# Add cron job or Cloud Scheduler to run:
python scripts/refresh_airtable_webhooks.py
```

### Verification

```bash
# Check webhook status
python -c "
from tools.airtable.webhooks import get_webhook_client
from shared.config.settings import get_settings

client = get_webhook_client()
settings = get_settings()

webhooks = client.list_webhooks(settings.airtable_base_id)
for w in webhooks:
    print(f'ID: {w[\"id\"]}')
    print(f'Enabled: {w[\"isHookEnabled\"]}')
    print(f'Expires: {w[\"expirationTime\"]}')
    print(f'URL: {w[\"notificationUrl\"]}')
    print()
"
```

## 🎯 Key Features

### 1. Automatic Table Discovery
The sync script reads `event_routing.yaml` and automatically determines which tables need monitoring based on your routing rules. No manual configuration needed!

### 2. Idempotent Operations
Safe to run sync script multiple times - it won't create duplicate webhooks.

### 3. Signature Verification
All webhooks are cryptographically verified using HMAC-SHA256, preventing unauthorized requests.

### 4. Custom Business Logic
Each table has its own handler with full Python capabilities. No limitations of Airtable's automation engine.

### 5. Scalable Architecture
Handlers publish to Pub/Sub for async processing. Cloud Run auto-scales to handle any load.

### 6. Version Controlled
All webhook logic is in Git. Easy to review, test, and deploy changes.

## 📊 Comparison to Manual Setup

### Before (Manual Airtable Webhooks)
```
❌ Manual webhook creation via Airtable UI
❌ Hard-coded notification URLs
❌ No signature verification
❌ Basic routing logic
❌ No version control
❌ Limited debugging
```

### After (Webhooks API Integration)
```
✅ Programmatic webhook management
✅ Auto-sync from routing config
✅ HMAC signature verification
✅ Custom per-table handlers
✅ Full Git integration
✅ Comprehensive logging
✅ Easy testing and debugging
```

## 🔒 Security

- **HMAC-SHA256 Verification**: Every webhook is cryptographically signed
- **HTTPS Only**: Cloud Run enforces TLS
- **Secret Management**: Webhook secrets stored in environment variables
- **Minimal Permissions**: Service account only needs Pub/Sub publish

## 🐛 Debugging

### View Recent Payloads
```python
from tools.airtable.webhooks import get_webhook_client
from shared.config.settings import get_settings

client = get_webhook_client()
settings = get_settings()

webhooks = client.list_webhooks(settings.airtable_base_id)
payloads = client.list_webhook_payloads(
    settings.airtable_base_id,
    webhooks[0]['id'],
    limit=10
)

for p in payloads['payloads']:
    print(f"{p['timestamp']}: {list(p['changedTablesById'].keys())}")
```

### Check Cloud Run Logs
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=jetsmx-webhooks" \
  --limit 50 \
  --format json
```

## 📈 Next Steps

### Add New Table
1. Create handler in `infra/webhooks/handlers/`
2. Register in `HANDLERS` dict
3. Add routing rules to `event_routing.yaml`
4. Re-sync (webhook already watches all tables!)

### Add Custom Logic
Edit the appropriate handler in `infra/webhooks/handlers/`. Changes deploy with next Cloud Run update.

### Monitor Health
Set up Cloud Monitoring alerts on:
- Webhook 4xx/5xx errors
- Handler exceptions
- Pub/Sub publish failures

## 📚 Documentation

- **Usage Guide**: `docs/AIRTABLE_WEBHOOKS_GUIDE.md`
- **Setup Steps**: `NEXT_STEPS.md` (Phase 5)
- **API Reference**: Inline docstrings in all modules

## ✨ Benefits

1. **No Polling**: Near real-time (< 1 second latency)
2. **Cost Effective**: Free webhooks vs paid automations
3. **Unlimited Logic**: Full Python instead of limited conditions
4. **Version Controlled**: All logic in Git
5. **Easy Testing**: Mock webhooks in tests
6. **Better Debugging**: Full stack traces and logs
7. **Scalable**: Auto-scales with Cloud Run
8. **Maintainable**: Clear separation of concerns

## 🎉 Status

**All TODOs completed!**

✅ Webhook API client  
✅ Signature verification  
✅ Handler framework  
✅ Auto-sync script  
✅ Webhook router  
✅ Configuration updates  
✅ Documentation  

**Ready for deployment!**

