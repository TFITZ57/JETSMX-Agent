# JetsMX Agent Framework - Next Steps

## ✅ What's Already Done
- ✅ Complete multi-agent system implemented (3 agents)
- ✅ 33 tools across 6 API integrations
- ✅ Cloud Run infrastructure code ready
- ✅ Pub/Sub event routing configured
- ✅ Documentation complete
- ✅ `.env` file created with all variables

---

## 🔴 CRITICAL: What You Need to Provide

### 1. Airtable Credentials (REQUIRED)
```bash
# Get these from Airtable
AIRTABLE_API_KEY=    # https://airtable.com/create/tokens
AIRTABLE_BASE_ID=    # From your base URL
```

**Where to find:**
- API Key: Airtable → Account → Generate API Token (needs full access to your base)
- Base ID: Open your Airtable base, check URL: `https://airtable.com/{BASE_ID}/...`

### 2. Google Chat Space ID (REQUIRED for human approvals)
```bash
GOOGLE_CHAT_SPACE_ID=    # From Chat URL or API
```

**Where to find:**
- Create a Google Chat space for JetsMX notifications
- Get space ID from URL or use Chat API to list spaces

### 3. Google Drive Folder IDs (REQUIRED)
```bash
DRIVE_FOLDER_RESUMES_INCOMING=       # Where resumes are uploaded
DRIVE_FOLDER_TRANSCRIPTS_PROBE=      # Where probe call transcripts go
DRIVE_FOLDER_TRANSCRIPTS_INTERVIEW=  # Where interview transcripts go
```

**Where to find:**
- Create these 3 folders in Google Drive
- Open each folder, copy ID from URL: `https://drive.google.com/drive/folders/{FOLDER_ID}`

### 4. Webhook Secret (RECOMMENDED)
```bash
WEBHOOK_SECRET=    # Generate random string for security
```

**How to generate:**
```bash
openssl rand -base64 32
```

---

## 📋 Setup Checklist

### Phase 1: Local Configuration (30 mins)
- [ ] **Edit `.env` file** - Fill in all `YOUR_*_HERE` values above
- [ ] **Verify `google-service-account-keys.json` exists** in project root
- [ ] **Install dependencies**: `pip install -r requirements.txt`
- [ ] **Test imports**: `python -c "from shared.config.settings import get_settings; print(get_settings())"`

### Phase 2: Airtable Setup (15 mins)
- [ ] **Create base** with these tables:
  - `applicants` - Applicant records
  - `applicant_pipeline` - Pipeline tracking
  - `interactions` - Audit log
  - `contractors` - Contractor records
  - `aircraft_types` - Reference data (optional)
  - `engine_families` - Reference data (optional)
  - `airports` - Reference data (optional)

- [ ] **Configure fields** according to `SCHEMA/airtable_schema.yaml`

### Phase 3: Google Cloud Setup (30 mins)
- [ ] **Verify Google Cloud Project** exists: `jetsmx-agent`
- [ ] **Enable APIs** in Google Cloud Console:
  - Cloud Run API
  - Cloud Pub/Sub API
  - Gmail API
  - Calendar API
  - Drive API
  - Chat API
  - Vertex AI API

- [ ] **Service Account Permissions** - Ensure your service account has:
  - `roles/run.admin` - Cloud Run deployment
  - `roles/pubsub.admin` - Pub/Sub management
  - `roles/aiplatform.user` - Vertex AI access
  - Domain-wide delegation for Workspace APIs

### Phase 4: Infrastructure Deployment (45 mins)
```bash
# 1. Create Pub/Sub topics and subscriptions
python scripts/setup_pubsub.py

# 2. Deploy Cloud Run services
chmod +x scripts/deploy_cloud_run.sh
./scripts/deploy_cloud_run.sh

# 3. Setup Gmail watch (must run every 7 days)
python scripts/setup_gmail_watch.py
```

### Phase 5: External Webhook Configuration (20 mins)
After Cloud Run deployment, you'll get URLs like:
- `https://jetsmx-webhooks-xxxxx.run.app`

- [ ] **Configure Airtable Webhook**:
  - Go to your base → Settings → Webhooks
  - Add webhook: `https://YOUR-WEBHOOK-URL/webhooks/airtable/applicant_pipeline`
  - Watch table: `applicant_pipeline`
  - Trigger on: Record updates

- [ ] **Configure Drive Watch** (if using file uploads):
  - Set watch on resume folder
  - Point to: `https://YOUR-WEBHOOK-URL/webhooks/drive`

### Phase 6: Testing (30 mins)
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests (requires real credentials)
pytest tests/integration/

# Manual workflow testing
python scripts/test_workflows.py all
```

---

## 🚀 Quick Start (If everything is configured)

```bash
# 1. Set environment variables
export $(cat .env | xargs)

# 2. Deploy infrastructure
python scripts/setup_pubsub.py
./scripts/deploy_cloud_run.sh
python scripts/setup_gmail_watch.py

# 3. Test end-to-end
python scripts/test_workflows.py all

# 4. Monitor logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

---

## 📊 What Each Component Does

### Agents
1. **Applicant Analysis** - Processes resumes, generates ICC reports, creates Airtable records
2. **HR Pipeline** - Sends emails, schedules meetings, updates pipeline stages
3. **Company KB** - Answers questions about applicants/contractors via Chat

### Infrastructure
- **Webhook Receiver** (Cloud Run) - Receives events from Airtable/Gmail/Drive/Chat
- **Pub/Sub Handler** (Cloud Run) - Routes events to appropriate agents

### Event Flow
```
External Event → Webhook → Pub/Sub → Handler → Agent → Tools → APIs
```

---

## 🔐 Security Notes

- Never commit `.env` to Git (already in `.gitignore`)
- Service account keys should have minimal required permissions
- Webhook secret provides signature verification
- All high-risk actions require human approval via Chat cards

---

## 📞 Need Help?

### Common Issues

**"Module not found" errors:**
```bash
pip install -r requirements.txt
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**"Permission denied" on Cloud Run:**
- Check service account has `roles/run.admin`
- Verify you're authenticated: `gcloud auth list`

**Gmail watch not working:**
- Verify domain-wide delegation is configured
- Check topic permissions allow Gmail to publish
- Watch expires after 7 days - re-run `setup_gmail_watch.py`

**Airtable webhook not triggering:**
- Verify webhook URL is publicly accessible
- Check Cloud Run service logs for incoming requests
- Ensure `WEBHOOK_SECRET` matches on both sides (if used)

---

## 📈 Monitoring & Maintenance

### Daily
- Monitor Cloud Run logs for errors
- Check Pub/Sub dead letter queues

### Weekly
- Renew Gmail watch (auto-expires after 7 days)
- Review interaction logs in Airtable

### Monthly
- Review API usage and costs
- Update dependencies: `pip install --upgrade -r requirements.txt`

---

## ✨ You're Ready to Go!

Once you've filled in the `.env` file with your credentials, run:

```bash
python scripts/setup_pubsub.py && ./scripts/deploy_cloud_run.sh
```

The system will be live and processing events automatically.

