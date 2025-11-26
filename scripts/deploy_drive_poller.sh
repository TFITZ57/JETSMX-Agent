#!/bin/bash
# Deploy Drive Folder Poller to Cloud Run

set -e

echo "======================================================================"
echo "Deploying Drive Folder Poller"
echo "======================================================================"

PROJECT_ID="jetsmx-agent"
REGION="us-central1"
SERVICE_NAME="jetsmx-drive-poller"

cd "$(dirname "$0")/.."

echo ""
echo "📦 Building and deploying to Cloud Run..."
echo ""

# Build and deploy using Cloud Build
gcloud builds submit \
  --config=infra/drive_poller/cloudbuild.yaml \
  --project=$PROJECT_ID

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
  --region $REGION \
  --project $PROJECT_ID \
  --platform managed \
  --allow-unauthenticated \
  --timeout=300 \
  --memory=512Mi \
  --concurrency=10 \
  --min-instances=0 \
  --max-instances=5 \
  --set-secrets=/secrets/google-service-account-keys.json=service-account-key:latest

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format='value(status.url)')

echo ""
echo "======================================================================"
echo "✅ Drive Poller Deployed Successfully"
echo "======================================================================"
echo "Service URL: $SERVICE_URL"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Deploy environment variables:"
echo "   python scripts/deploy_env_to_cloud_run.py --yes"
echo ""
echo "2. Setup scheduler (polls every 2 minutes):"
echo "   python scripts/setup_drive_poller_scheduler.py \\"
echo "     $SERVICE_URL \\"
echo "     jetsmx-hr-agent@jetsmx-agent.iam.gserviceaccount.com"
echo ""
echo "3. Test manually:"
echo "   curl $SERVICE_URL"
echo ""
echo "======================================================================"

