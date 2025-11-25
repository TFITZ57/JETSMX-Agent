# 🚀 Quick Setup Summary

## What You Need to Do

### 1️⃣ Create .env File (5 mins)

**Option A: Interactive (Recommended)**
```bash
python scripts/setup_env.py
```

**Option B: Manual**
```bash
cp env.template .env
nano .env  # or code .env
```

### 2️⃣ Get These Credentials

| Credential | Where to Get It | Status |
|------------|----------------|--------|
| **AIRTABLE_API_KEY** | https://airtable.com/create/tokens | 🔴 REQUIRED |
| **AIRTABLE_BASE_ID** | From your base URL | 🔴 REQUIRED |
| **GOOGLE_CHAT_SPACE_ID** | Create Chat space, get ID | 🔴 REQUIRED |
| **DRIVE_FOLDER_RESUMES_INCOMING** | Create Drive folder, copy ID from URL | 🔴 REQUIRED |
| **DRIVE_FOLDER_TRANSCRIPTS_PROBE** | Create Drive folder, copy ID from URL | 🔴 REQUIRED |
| **DRIVE_FOLDER_TRANSCRIPTS_INTERVIEW** | Create Drive folder, copy ID from URL | 🔴 REQUIRED |
| **WEBHOOK_SECRET** | `openssl rand -base64 32` | 🟡 RECOMMENDED |

### 3️⃣ Verify Setup (2 mins)

```bash
# Check service account exists
ls -la google-service-account-keys.json

# Test config loads
python -c "from shared.config.settings import get_settings; print(get_settings())"

# Install dependencies (if not done)
pip install -r requirements.txt
```

### 4️⃣ Deploy Infrastructure (15 mins)

```bash
# Create Pub/Sub topics
python scripts/setup_pubsub.py

# Deploy Cloud Run services
chmod +x scripts/deploy_cloud_run.sh
./scripts/deploy_cloud_run.sh

# Setup Gmail watch
python scripts/setup_gmail_watch.py
```

---

## Files Created for You

✅ **env.template** - Template with all environment variables  
✅ **NEXT_STEPS.md** - Complete deployment guide  
✅ **CREDENTIALS_NEEDED.md** - Detailed credential instructions  
✅ **SETUP_SUMMARY.md** - This quick reference (you are here)  
✅ **scripts/setup_env.py** - Interactive env setup script  

---

## Quick Airtable Setup

Your Airtable base needs these tables:

```
1. applicants          - Main applicant records
2. applicant_pipeline  - Pipeline tracking
3. interactions        - Audit log
4. contractors         - Contractor records
```

See `SCHEMA/airtable_schema.yaml` for field details.

---

## Quick Drive Setup

Create 3 folders in Google Drive:

```
JetsMX/
├── Resumes - Incoming/
├── Transcripts - Probe Calls/
└── Transcripts - Interviews/
```

Copy each folder ID from URL: `drive.google.com/drive/folders/{FOLDER_ID}`

---

## Quick Google Chat Setup

1. Create a new Chat space: "JetsMX Agent Notifications"
2. Add the service account as a member (optional)
3. Get the space ID from the URL or API

---

## Test Everything Works

```bash
# Test 1: Config loads
python -c "from shared.config.settings import get_settings; s = get_settings(); print(f'✅ Project: {s.gcp_project_id}')"

# Test 2: Airtable connects
python -c "from tools.airtable.client import AirtableClient; c = AirtableClient(); print('✅ Airtable OK')"

# Test 3: Google auth works
python -c "from shared.auth.google_auth import get_credentials; creds = get_credentials(); print('✅ Google Auth OK')"

# Test 4: Run all tests
pytest tests/unit/
```

---

## Common Issues

**"No module named 'shared'"**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**"google-service-account-keys.json not found"**
- Make sure the file exists in project root
- Check `GCP_SERVICE_ACCOUNT_JSON_PATH` in `.env`

**"Invalid Airtable credentials"**
- Verify API token at https://airtable.com/create/tokens
- Ensure token has full access to your base

**"Permission denied" on Cloud Run**
- Check service account has `roles/run.admin`
- Run: `gcloud auth list` to verify authentication

---

## Deployment Checklist

- [ ] `.env` file created with all credentials
- [ ] `google-service-account-keys.json` exists
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Airtable base created with required tables
- [ ] Drive folders created and IDs copied
- [ ] Google Chat space created and ID copied
- [ ] Google Cloud APIs enabled (Run, Pub/Sub, Vertex AI, Workspace APIs)
- [ ] Service account has domain-wide delegation
- [ ] Pub/Sub topics created: `python scripts/setup_pubsub.py`
- [ ] Cloud Run services deployed: `./scripts/deploy_cloud_run.sh`
- [ ] Gmail watch configured: `python scripts/setup_gmail_watch.py`
- [ ] Airtable webhook pointing to Cloud Run URL
- [ ] Tests passing: `pytest tests/`

---

## Architecture Diagram

```
External Events
    ↓
Webhooks (Cloud Run)
    ↓
Pub/Sub Topics
    ↓
Event Router (Cloud Run)
    ↓
Agents (Vertex AI + Gemini)
    ↓
Tools (33 functions)
    ↓
APIs (Airtable, Gmail, Drive, Calendar, Chat)
```

---

## Need More Details?

- **CREDENTIALS_NEEDED.md** - Detailed credential instructions
- **NEXT_STEPS.md** - Full deployment guide with troubleshooting
- **docs/deployment.md** - Production deployment guide
- **docs/architecture.md** - System architecture details
- **README.md** - Project overview

---

## Once Everything is Set Up

The system runs automatically:

1. Resume uploaded to Drive → Agent analyzes → Creates Airtable record
2. HR updates pipeline in Airtable → Agent generates email draft
3. Applicant replies to email → Agent parses, updates pipeline
4. Transcript uploaded → Agent analyzes, updates profile
5. All actions logged to `interactions` table

Human approval required for:
- Sending emails
- Scheduling calls
- High-risk actions

Approvals happen via Google Chat interactive cards.

---

## 🎉 You're Ready!

Once `.env` is filled in, run:

```bash
python scripts/setup_env.py  # or manually edit .env
python scripts/setup_pubsub.py
./scripts/deploy_cloud_run.sh
```

System will be live and processing events.

