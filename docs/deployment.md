# JetsMX Agent Framework - Deployment Guide

## Prerequisites

1. **Google Cloud Project**: `jetsmx-agent`
2. **Service Account**: Created with appropriate IAM permissions
3. **API Enablement**: Enable the following APIs:
   - Cloud Run API
   - Cloud Pub/Sub API
   - Gmail API
   - Calendar API
   - Drive API
   - Chat API
   - Vertex AI API

## Setup Steps

### 1. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# - Add Airtable API key and base ID
# - Configure folder IDs for Drive
# - Set Chat space ID
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create Pub/Sub Topics

```bash
python scripts/setup_pubsub.py
```

This creates:
- `jetsmx-airtable-events`
- `jetsmx-gmail-events`
- `jetsmx-drive-events`
- `jetsmx-chat-events`

### 4. Deploy Cloud Run Services

```bash
# Make script executable
chmod +x scripts/deploy_cloud_run.sh

# Deploy
./scripts/deploy_cloud_run.sh
```

This deploys:
- **Webhook Receiver**: Public-facing endpoint for webhooks
- **Pub/Sub Handler**: Internal service for processing events

### 5. Configure Gmail Watch & Automated Renewal

#### Initial Setup

```bash
python scripts/setup_gmail_watch.py
```

#### Automated Renewal with Cloud Scheduler

Gmail watch expires after 7 days, so set up Cloud Scheduler to automatically renew it every 6 days:

```bash
# Get your Cloud Run service URL
WEBHOOK_URL=$(gcloud run services describe jetsmx-webhooks --region us-central1 --format='value(status.url)')

# Get your service account email (use existing service account)
SERVICE_ACCOUNT="jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com"

# Setup the scheduler
python scripts/setup_gmail_watch_scheduler.py $WEBHOOK_URL $SERVICE_ACCOUNT
```

This creates a Cloud Scheduler job that:
- Runs every 6 days at midnight UTC
- POSTs to `/internal/scheduler/renew-gmail-watch` on your Cloud Run service
- Uses OIDC authentication for secure internal calls
- Retries up to 3 times with exponential backoff on failure

**Monitoring the Scheduler:**

```bash
# List scheduler jobs
gcloud scheduler jobs list --location=us-central1

# View job details
gcloud scheduler jobs describe gmail-watch-renewal --location=us-central1

# Manually trigger for testing
gcloud scheduler jobs run gmail-watch-renewal --location=us-central1

# Check logs
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.message=~'Gmail watch'" --limit 10
```

### 6. Configure External Webhooks

#### Airtable Webhooks
1. Go to Airtable base settings
2. Navigate to Webhooks
3. Add webhook URL: `https://your-webhook-url/webhooks/airtable/applicant_pipeline`
4. Select "Applicant Pipeline" table
5. Enable for record updates

#### Drive File Notifications
1. Set up watch on resume folder
2. Configure webhook to Cloud Run service
3. Filter for PDF files only

## Vertex AI Agent Deployment

Agents are deployed to Vertex AI Agent Builder for hosting:

```python
# Deploy applicant analysis agent
python infra/vertex_deploy/deploy_agents.py --agent applicant_analysis

# Deploy all agents
python infra/vertex_deploy/deploy_agents.py --all
```

## Testing

### Unit Tests

```bash
pytest tests/unit/
```

### Integration Tests

```bash
pytest tests/integration/
```

### Manual Workflow Tests

```bash
# Test applicant analysis
python scripts/test_workflows.py applicant_analysis

# Test HR pipeline
python scripts/test_workflows.py hr_pipeline

# Test company KB
python scripts/test_workflows.py company_kb

# Test all
python scripts/test_workflows.py all
```

## Monitoring

### Cloud Run Logs

```bash
# Webhook receiver logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=jetsmx-webhooks" --limit 50

# Pub/Sub handler logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=jetsmx-pubsub-handler" --limit 50
```

### Pub/Sub Metrics

View in Google Cloud Console:
- Pub/Sub → Topics → Select topic → Metrics

## Troubleshooting

### Gmail Watch Not Working

- Check topic permissions
- Verify service account has domain-wide delegation
- Ensure Gmail API is enabled
- Check Cloud Scheduler job status: `gcloud scheduler jobs describe gmail-watch-renewal --location=us-central1`
- Verify automatic renewal is working: Check logs for renewal messages
- Manually trigger renewal if needed: `gcloud scheduler jobs run gmail-watch-renewal --location=us-central1`

### Webhooks Not Triggering

- Verify webhook URL is public (for Airtable)
- Check Cloud Run service logs
- Verify signature validation (if enabled)
- Test with curl:

```bash
curl -X POST https://your-webhook-url/webhooks/airtable/applicant_pipeline \
  -H "Content-Type: application/json" \
  -d '{"table_id":"applicant_pipeline","record_id":"test"}'
```

### Agent Errors

- Check Vertex AI logs
- Verify tool permissions in config
- Ensure LLM has access to required APIs
- Review agent prompts for clarity

## Scaling Considerations

- **Cloud Run**: Auto-scales based on requests
- **Pub/Sub**: Handles high throughput automatically
- **Vertex AI**: Managed scaling for agent invocations

## Security

- Service account keys stored securely (not in repo)
- Webhook signature verification enabled
- Cloud Run services use least-privilege IAM
- Airtable API key environment variable only

## Cost Optimization

- Use Cloud Run minimum instances: 0 (scale to zero)
- Set Pub/Sub subscription acknowledgment deadlines appropriately
- Monitor Vertex AI API usage
- Use Cloud Scheduler for periodic tasks (e.g., Gmail watch renewal)

