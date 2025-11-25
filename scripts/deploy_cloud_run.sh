#!/bin/bash
# Deploy Cloud Run services for JetsMX Agent

set -e

PROJECT_ID="jetsmx-agent"
REGION="us-central1"

echo "Deploying JetsMX Cloud Run services..."

# Deploy webhook receiver (build from project root)
echo "Building and deploying webhook receiver..."
gcloud builds submit --config=infra/webhooks/cloudbuild.yaml .
gcloud run deploy jetsmx-webhooks \
  --image gcr.io/${PROJECT_ID}/jetsmx-webhooks \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=${PROJECT_ID}

WEBHOOK_URL=$(gcloud run services describe jetsmx-webhooks --platform managed --region ${REGION} --format 'value(status.url)')
echo "Webhook receiver deployed: ${WEBHOOK_URL}"

# Deploy Pub/Sub handler (build from project root)
echo "Building and deploying Pub/Sub handler..."
gcloud builds submit --config=infra/pubsub_handlers/cloudbuild.yaml .
gcloud run deploy jetsmx-pubsub-handler \
  --image gcr.io/${PROJECT_ID}/jetsmx-pubsub-handler \
  --platform managed \
  --region ${REGION} \
  --no-allow-unauthenticated \
  --set-env-vars PROJECT_ID=${PROJECT_ID}

PUBSUB_URL=$(gcloud run services describe jetsmx-pubsub-handler --platform managed --region ${REGION} --format 'value(status.url)')
echo "Pub/Sub handler deployed: ${PUBSUB_URL}"

echo ""
echo "Deployment complete!"
echo "Webhook receiver: ${WEBHOOK_URL}"
echo "Pub/Sub handler: ${PUBSUB_URL}"
echo ""
echo "Next steps:"
echo "1. Update Pub/Sub subscriptions with the handler URL"
echo "2. Configure Airtable webhooks to point to ${WEBHOOK_URL}/webhooks/airtable/applicant_pipeline"
echo "3. Run setup_gmail_watch.py to enable Gmail notifications"

