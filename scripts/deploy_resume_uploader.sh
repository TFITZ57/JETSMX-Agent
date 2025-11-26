#!/bin/bash
# Deploy Resume Uploader Web Interface to Cloud Run

set -e

echo "======================================================================"
echo "Deploying Resume Uploader"
echo "======================================================================"

PROJECT_ID="jetsmx-agent"
REGION="us-central1"
SERVICE_NAME="jetsmx-resume-uploader"

cd "$(dirname "$0")/.."

echo ""
echo "📦 Building and deploying to Cloud Run..."
echo ""

# Build using Cloud Build
gcloud builds submit \
  --config=infra/resume_uploader/cloudbuild.yaml \
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
  --concurrency=80 \
  --min-instances=0 \
  --max-instances=10 \
  --set-secrets=/secrets/google-service-account-keys.json=service-account-key:latest

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format='value(status.url)')

echo ""
echo "======================================================================"
echo "✅ Resume Uploader Deployed Successfully"
echo "======================================================================"
echo "Service URL: $SERVICE_URL"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Deploy environment variables:"
echo "   python scripts/deploy_env_to_cloud_run.py --yes"
echo ""
echo "2. Open in browser:"
echo "   open $SERVICE_URL"
echo ""
echo "3. Share with team:"
echo "   $SERVICE_URL"
echo ""
echo "======================================================================"

