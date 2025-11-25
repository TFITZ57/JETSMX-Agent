# 🔑 Credentials & IDs You Need to Provide

## Quick Reference - Fill These In

```bash
# Copy the example env file
cp .env.example .env
```

Then edit `.env` and replace these placeholders:

---

## 1. Airtable (REQUIRED)

### AIRTABLE_API_KEY
**What:** Your Airtable personal access token  
**Get it:** https://airtable.com/create/tokens  
**Permissions needed:** Full access to your JetsMX base  
**Example:** `patAbcDef123456789.1234567890abcdefghijklmnopqrstuvwxyz`

### AIRTABLE_BASE_ID
**What:** The unique ID of your Airtable base  
**Get it:** Open your base, look at the URL: `https://airtable.com/appXXXXXXXXXXXXXX/...`  
**Example:** `appAbcDef123456`

---

## 2. Google Chat (REQUIRED for approvals)

### GOOGLE_CHAT_SPACE_ID
**What:** The space where the bot will post approval cards  
**Get it:** 
- Option 1: Create a Chat space, get ID from URL
- Option 2: Use Chat API to list spaces: 
  ```python
  from tools.chat.client import ChatClient
  client = ChatClient()
  spaces = client.list_spaces()
  print(spaces)
  ```
**Example:** `spaces/AAAAxxxxxxx`

---

## 3. Google Drive (REQUIRED)

### DRIVE_FOLDER_RESUMES_INCOMING
**What:** Folder where new resume PDFs are uploaded  
**Get it:** 
1. Create folder in Drive: "JetsMX Resumes - Incoming"
2. Open folder, copy ID from URL: `https://drive.google.com/drive/folders/1AbC...XyZ`
**Example:** `1AbCdEfGhIjKlMnOpQrStUvWxYz0123456`

### DRIVE_FOLDER_TRANSCRIPTS_PROBE
**What:** Folder for probe call transcripts  
**Get it:** Same as above, create "JetsMX Transcripts - Probe Calls"  
**Example:** `1BcDeFgHiJkLmNoPqRsTuVwXyZ1234567`

### DRIVE_FOLDER_TRANSCRIPTS_INTERVIEW
**What:** Folder for interview transcripts  
**Get it:** Same as above, create "JetsMX Transcripts - Interviews"  
**Example:** `1CdEfGhIjKlMnOpQrStUvWxYz2345678`

---

## 4. Webhook Secret (RECOMMENDED)

### WEBHOOK_SECRET
**What:** Random string to verify webhook authenticity  
**Generate it:**
```bash
openssl rand -base64 32
```
**Example:** `dGhpc2lzYXNlY3VyZXJhbmRvbXN0cmluZ2Zvcndl`

---

## 5. Already Configured (verify these)

### GCP_PROJECT_ID
**Current value:** `jetsmx-agent`  
**Action:** Verify this project exists in your Google Cloud Console

### GCP_SERVICE_ACCOUNT_JSON_PATH
**Current value:** `./google-service-account-keys.json`  
**Action:** Verify this file exists in project root

### GMAIL_USER_EMAIL
**Current value:** `jobs@jetstreammx.com`  
**Action:** Verify this is the correct email for hiring communications

### VERTEX_AI_LOCATION
**Current value:** `us-central1`  
**Action:** Change if you prefer a different region

---

## Quick Setup Commands

```bash
# 1. Copy template
cp .env.example .env

# 2. Generate webhook secret
echo "WEBHOOK_SECRET=$(openssl rand -base64 32)" >> .env

# 3. Edit .env and fill in the rest
nano .env
# or
code .env

# 4. Verify it loads
python -c "from shared.config.settings import get_settings; s = get_settings(); print(f'✅ Loaded: {s.gcp_project_id}')"
```

---

## What Happens If You Don't Provide Something?

| Missing | Impact |
|---------|--------|
| `AIRTABLE_API_KEY` | ❌ System won't start - required |
| `AIRTABLE_BASE_ID` | ❌ System won't start - required |
| `GOOGLE_CHAT_SPACE_ID` | ⚠️ Approval cards won't work - agents can't send notifications |
| `DRIVE_FOLDER_*` | ⚠️ Resume processing won't work - can't find files |
| `WEBHOOK_SECRET` | ⚠️ Webhooks will work but less secure |

---

## Validation Checklist

After filling in `.env`:

```bash
# Test 1: Settings load correctly
python -c "from shared.config.settings import get_settings; s = get_settings(); print('✅ Settings loaded')"

# Test 2: Airtable connection
python -c "from tools.airtable.client import AirtableClient; c = AirtableClient(); print('✅ Airtable connected')"

# Test 3: Google auth works
python -c "from shared.auth.google_auth import get_credentials; creds = get_credentials(); print('✅ Google auth works')"
```

---

## Security Reminders

- ❌ **NEVER** commit `.env` to Git (already in `.gitignore`)
- ✅ Keep `google-service-account-keys.json` secure
- ✅ Rotate `AIRTABLE_API_KEY` if it's ever exposed
- ✅ Use `WEBHOOK_SECRET` to verify webhook requests
- ✅ Limit service account permissions to only what's needed

