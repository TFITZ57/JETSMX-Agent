# Gmail Watch Manual Renewal

## Overview

Gmail push notifications expire after 7 days. Due to Cloud Run's requirement for domain-wide delegation with service account keys (not available via Application Default Credentials), the automated renewal via Cloud Scheduler doesn't work.

**Current Status:**
- ✅ Airtable webhook auto-refresh: **Working** (every 5 days)
- ⚠️ Gmail watch renewal: **Manual** (every 7 days)

## Manual Renewal Process

Run this command every 7 days to renew the Gmail watch:

```bash
python scripts/setup_gmail_watch.py
```

This will:
- Set up Gmail push notifications for `jobs@jetstreammx.com`
- Subscribe to the `jetsmx-gmail-events` Pub/Sub topic
- Extend the watch for another 7 days

## Checking Current Status

View the current Gmail watch expiration:

```bash
python -c "
from tools.gmail.client import get_gmail_client
import datetime

client = get_gmail_client()
profile = client.service.users().getProfile(userId='me').execute()
print(f'Gmail: {profile[\"emailAddress\"]}')

# Note: Gmail API doesn't expose watch expiration directly
# You need to track it manually or check Cloud Logging
"
```

## Setting Up Automated Renewal (Advanced)

To enable automated renewal, you need to configure the service account key as a Cloud Run secret:

### Option 1: Service Account Key Secret (Recommended)

```bash
# 1. Create secret
gcloud secrets create jetsmx-service-account-key \
  --data-file=google-service-account-keys.json \
  --project=jetsmx-agent

# 2. Grant access
gcloud secrets add-iam-policy-binding jetsmx-service-account-key \
  --member="serviceAccount:jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=jetsmx-agent

# 3. Update deployment script to mount secret
# Add to scripts/deploy_cloud_run.sh:
# --update-secrets=/secrets/service-account.json=jetsmx-service-account-key:latest \
# --set-env-vars GCP_SERVICE_ACCOUNT_JSON_PATH=/secrets/service-account.json
```

### Option 2: Domain-Wide Delegation Setup

Configure domain-wide delegation for the Cloud Run service account in Google Workspace Admin Console:

1. Go to Google Admin Console → Security → API Controls → Domain-wide Delegation
2. Add Client ID: `jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com`
3. Add OAuth Scopes:
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/drive`

**Note:** This approach may not work with Application Default Credentials. The service account key file is still recommended.

## Monitoring

Check Gmail watch status in Cloud Logging:

```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND 
   resource.labels.service_name=jetsmx-webhooks AND 
   jsonPayload.message=~'Gmail watch'" \
  --limit=10 \
  --project=jetsmx-agent
```

## Workaround Status

**Current Implementation:**
- Agents work fully for Airtable-triggered workflows ✅
- Gmail notifications work for 7 days after manual renewal ✅  
- Automatic renewal via Cloud Scheduler: **Pending** (requires secret mount or domain-wide delegation)

**Impact:**
- Low: Gmail watch is for incoming email processing
- Main workflow (Airtable pipeline updates) is unaffected
- Manual renewal takes < 1 minute every 7 days

## Future Improvements

1. **Implement secret mounting** for service account keys
2. **Add expiration tracking** to log upcoming renewals
3. **Create monitoring alert** for expired watches
4. **Document renewal in runbook** for operations team

