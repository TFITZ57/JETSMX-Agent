# Cloud Scheduler Setup

Automated maintenance tasks for the JetsMX Agent Framework.

## Overview

The system uses Google Cloud Scheduler to automatically maintain:

1. **Gmail Watch Renewal** - Renews Gmail push notifications every 6 days (expires after 7 days)
2. **Airtable Webhook Refresh** - Refreshes Airtable webhooks every 5 days (expires after 7 days)

## Architecture

```
Cloud Scheduler (cron) → Cloud Run (webhook service) → API calls
    ↓                         ↓                            ↓
Every 5-6 days          /internal/scheduler/*      Gmail/Airtable APIs
```

## Scheduler Jobs

### 1. Airtable Webhook Refresh

- **Job Name**: `airtable-webhook-refresh`
- **Schedule**: Every 5 days at midnight UTC (`0 0 */5 * *`)
- **Endpoint**: `/internal/scheduler/refresh-airtable-webhooks`
- **Purpose**: Prevents Airtable webhooks from expiring due to inactivity

### 2. Gmail Watch Renewal

- **Job Name**: `gmail-watch-renewal`
- **Schedule**: Every 6 days at midnight UTC (`0 0 */6 * *`)
- **Endpoint**: `/internal/scheduler/renew-gmail-watch`
- **Purpose**: Renews Gmail push notification watch before 7-day expiration

## Setup

### Prerequisites

1. Cloud Scheduler API enabled
2. Cloud Run service deployed (`jetsmx-webhooks`)
3. Service account with OIDC token auth configured
4. Service account key stored in Secret Manager (see Setup section)
5. Gmail API service account granted Pub/Sub publisher permissions

### Setup Service Account Secret (Required for Gmail Watch)

The Gmail watch renewal requires domain-wide delegation, which needs the service account key file. Store it securely in Secret Manager:

```bash
# Create secret from service account key file
gcloud secrets create service-account-key \
  --data-file=google-service-account-keys.json \
  --project=jetsmx-agent

# Grant service account access to the secret
gcloud secrets add-iam-policy-binding service-account-key \
  --member="serviceAccount:jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=jetsmx-agent

# Grant Gmail API permission to publish to Pub/Sub topic
gcloud pubsub topics add-iam-policy-binding jetsmx-gmail-events \
  --member="serviceAccount:gmail-api-push@system.gserviceaccount.com" \
  --role="roles/pubsub.publisher" \
  --project=jetsmx-agent
```

The `deploy_cloud_run.sh` script automatically mounts this secret to Cloud Run services.

### Create Schedulers

```bash
# Setup both schedulers at once
python scripts/setup_all_schedulers.py \
  https://jetsmx-webhooks-wg3iuj477q-uc.a.run.app \
  jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com

# Or setup individually
python scripts/setup_airtable_webhook_scheduler.py \
  https://jetsmx-webhooks-wg3iuj477q-uc.a.run.app \
  jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com

python scripts/setup_gmail_watch_scheduler.py \
  https://jetsmx-webhooks-wg3iuj477q-uc.a.run.app \
  jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com
```

## Management

### List All Scheduler Jobs

```bash
gcloud scheduler jobs list \
  --location=us-central1 \
  --project=jetsmx-agent
```

### Check Job Details

```bash
# Airtable webhook refresh
gcloud scheduler jobs describe airtable-webhook-refresh \
  --location=us-central1 \
  --project=jetsmx-agent

# Gmail watch renewal
gcloud scheduler jobs describe gmail-watch-renewal \
  --location=us-central1 \
  --project=jetsmx-agent
```

### Manually Trigger Jobs

```bash
# Trigger Airtable webhook refresh
gcloud scheduler jobs run airtable-webhook-refresh \
  --location=us-central1 \
  --project=jetsmx-agent

# Trigger Gmail watch renewal
gcloud scheduler jobs run gmail-watch-renewal \
  --location=us-central1 \
  --project=jetsmx-agent
```

### View Execution Logs

```bash
# View Cloud Run logs for scheduler endpoints
gcloud logging read "resource.type=cloud_run_revision AND 
  resource.labels.service_name=jetsmx-webhooks AND 
  jsonPayload.message=~'scheduler'" \
  --limit=50 \
  --project=jetsmx-agent \
  --format=json
```

## Endpoints

### POST /internal/scheduler/refresh-airtable-webhooks

Refreshes all Airtable webhooks for the configured base.

**Response:**
```json
{
  "status": "success",
  "message": "Refreshed N Airtable webhooks",
  "webhooks_refreshed": 1,
  "webhooks": [
    {
      "webhook_id": "achXXXXXXXXXXXXXX",
      "old_expiration": "2025-12-02T20:28:28.864Z",
      "new_expiration": "2025-12-07T20:33:50.123Z"
    }
  ]
}
```

### POST /internal/scheduler/renew-gmail-watch

Renews Gmail watch subscription.

**Response:**
```json
{
  "status": "success",
  "message": "Gmail watch renewed successfully",
  "history_id": "123456",
  "expiration": "1733356800000"
}
```

## Retry Configuration

Both jobs use the same retry configuration:

- **Retry count**: 3 attempts
- **Max retry duration**: 1 hour
- **Min backoff**: 1 minute
- **Max backoff**: 10 minutes
- **Max doublings**: 3

## Authentication

Scheduler jobs use **OIDC token authentication** with the service account:
- `jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com`

This provides secure, authenticated requests to Cloud Run without managing API keys.

## Monitoring

### Check Last Execution

```bash
# View last execution time and status
gcloud scheduler jobs describe airtable-webhook-refresh \
  --location=us-central1 \
  --format="value(status.lastAttemptTime,status.code)"
```

### Set Up Alerts

Create alert policies in Cloud Monitoring for:

1. **Job Failures**: Alert when `status.code != 0`
2. **No Recent Execution**: Alert if `lastAttemptTime` is > 7 days old
3. **Webhook Expiration**: Alert if Airtable webhooks haven't been refreshed in 6+ days

## Troubleshooting

### Job Not Running

```bash
# Check job state
gcloud scheduler jobs describe airtable-webhook-refresh \
  --location=us-central1

# Check for execution errors
gcloud logging read "resource.type=cloud_scheduler_job AND 
  resource.labels.job_id=airtable-webhook-refresh" \
  --limit=10 \
  --project=jetsmx-agent
```

### 403 Permission Denied

Ensure service account has:
- `roles/run.invoker` on Cloud Run service
- Service account is configured in OIDC token

```bash
gcloud run services add-iam-policy-binding jetsmx-webhooks \
  --region=us-central1 \
  --member="serviceAccount:jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### Endpoint Returns Error

Test the endpoint directly:

```bash
# Get ID token for service account
gcloud auth print-identity-token \
  --impersonate-service-account=jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com

# Test endpoint
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-identity-token --impersonate-service-account=jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com)" \
  https://jetsmx-webhooks-wg3iuj477q-uc.a.run.app/internal/scheduler/refresh-airtable-webhooks
```

## Cost Considerations

- Cloud Scheduler: $0.10/job/month (first 3 jobs free)
- Cloud Run invocations: Minimal (2-4x per week)
- Total estimated cost: **~$0.20/month** or **free** (within free tier)

## Manual Alternatives

If you need to run these tasks manually instead:

```bash
# Refresh Airtable webhooks
python scripts/refresh_airtable_webhooks.py

# Renew Gmail watch
python scripts/setup_gmail_watch.py
```

