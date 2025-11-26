# Batch Resume Processing

Process existing resumes that are already in your Google Drive folder.

## Quick Start

### Process All Resumes (with 2-second delay)
```bash
python scripts/process_existing_resumes.py
```

### Process First 10 Resumes (testing)
```bash
python scripts/process_existing_resumes.py 2 0 10
```

### Process in Batches of 10
```bash
# Batch 1: Files 0-9
python scripts/process_existing_resumes.py 2 0 10

# Batch 2: Files 10-19
python scripts/process_existing_resumes.py 2 10 20

# Batch 3: Files 20-29
python scripts/process_existing_resumes.py 2 20 30

# And so on...
```

---

## Command Syntax

```bash
python scripts/process_existing_resumes.py [DELAY] [START_INDEX] [END_INDEX]
```

**Parameters:**
- `DELAY` (optional): Seconds to wait between each file (default: 2)
  - Use `0` for no delay (not recommended for large batches)
  - Use `5` for slower processing (safer for 40+ files)
  
- `START_INDEX` (optional): Start from this file number (0-based, default: 0)
- `END_INDEX` (optional): Stop before this file number (exclusive, default: all files)

---

## Examples

### 1. Process All 40 Resumes at Once
```bash
python scripts/process_existing_resumes.py 2
```
- **Time:** ~2 minutes (2 seconds × 40 files)
- **Best for:** When you want everything processed now
- **Note:** Agent will process them as fast as it can

### 2. Test with First 5 Resumes
```bash
python scripts/process_existing_resumes.py 2 0 5
```
- **Time:** ~10 seconds
- **Best for:** Testing before full batch
- **Verify:** Check Airtable after 1 minute to confirm they processed

### 3. Process in Smaller Batches (Recommended)
```bash
# Morning batch
python scripts/process_existing_resumes.py 3 0 10

# Wait 10 minutes, check results, then:
# Afternoon batch
python scripts/process_existing_resumes.py 3 10 20

# Evening batch
python scripts/process_existing_resumes.py 3 20 30

# Next day
python scripts/process_existing_resumes.py 3 30 40
```
- **Time:** Spread over hours/days
- **Best for:** Being conservative, monitoring quality
- **Safer:** Can catch issues early

### 4. Process One at a Time (Manual Verification)
```bash
python scripts/process_existing_resumes.py 0 0 1   # First resume
python scripts/process_existing_resumes.py 0 1 2   # Second resume
python scripts/process_existing_resumes.py 0 2 3   # Third resume
```
- **Best for:** High-value candidates you want to check individually

---

## What Happens

For each resume file:

1. **Script publishes event to Pub/Sub** (~0.5 seconds)
2. **Pub/Sub triggers Applicant Agent** (immediately)
3. **Agent processes resume:**
   - Downloads PDF from Drive
   - Extracts text and parses fields
   - Analyzes with OpenAI (~10-20 seconds)
   - Creates Airtable records
   - Generates ICC PDF
   - Uploads ICC to Drive
   - **Total: 30-60 seconds per resume**

### Timeline Example (40 resumes)

**If you process all at once:**
- Events published: 2 minutes
- Agent processing: 20-40 minutes (runs in parallel)
- **Total: ~40 minutes until all done**

**If you process in batches of 10:**
- Batch 1: 20 seconds to publish → 10 minutes to process
- Wait 5 minutes
- Batch 2: 20 seconds to publish → 10 minutes to process
- **Total: ~1 hour (more controlled)**

---

## Monitoring Progress

### Check Pub/Sub Events
```bash
# See events being published
gcloud logging read "resource.labels.service_name=jetsmx-resume-uploader OR textPayload=~'resume'" --limit=20 --project=jetsmx-agent
```

### Check Agent Processing
```bash
# See agent activity
gcloud logging read "resource.labels.service_name=jetsmx-pubsub-handler AND textPayload=~'resume'" --limit=30 --project=jetsmx-agent

# See just successes
gcloud logging read "resource.labels.service_name=jetsmx-pubsub-handler AND textPayload=~'✓'" --limit=30 --project=jetsmx-agent

# See errors
gcloud logging read "resource.labels.service_name=jetsmx-pubsub-handler AND severity>=ERROR" --limit=20 --project=jetsmx-agent
```

### Check Airtable
1. Open your Airtable base
2. Go to Applicants table
3. Sort by "Created Time" (newest first)
4. You should see new records appearing

---

## Rate Limiting & Safety

### Recommended Settings for 40 Resumes

**Option 1: All at once (fastest)**
```bash
python scripts/process_existing_resumes.py 2
```
- ✅ Fast (done in 40 min)
- ⚠️ No intermediate checks
- Best if: You trust the system

**Option 2: Batches of 10 (safer)**
```bash
python scripts/process_existing_resumes.py 3 0 10
# Wait 10-15 min, verify, then next batch
python scripts/process_existing_resumes.py 3 10 20
# And so on...
```
- ✅ Can verify quality between batches
- ✅ Can stop if you see issues
- Best if: First time using batch processing

**Option 3: Very slow (most cautious)**
```bash
python scripts/process_existing_resumes.py 5 0 10
```
- ✅ Gives system plenty of breathing room
- ⚠️ Takes longer (5 sec/file)
- Best if: You're seeing errors with faster settings

---

## Troubleshooting

### Error: "Failed to list files"
**Solution:** Run this to test Drive access:
```bash
python -c "from tools.drive.files import list_files_in_folder; from shared.config.settings import get_settings; s=get_settings(); print(list_files_in_folder(s.drive_folder_resumes_incoming))"
```

### Error: "Failed to publish event"
**Solution:** Check Pub/Sub topic exists:
```bash
gcloud pubsub topics list --project=jetsmx-agent | grep drive
```

### Resumes Not Processing
**Check:**
1. Events published? (script says "✅ Event published")
2. Agent receiving? Check logs above
3. OpenAI API key set? Check environment variables

### Some Resumes Failed
**Retry failed files:**
The script will show which files failed. Note the index numbers and run:
```bash
# If files 15, 23, and 34 failed:
python scripts/process_existing_resumes.py 0 15 16
python scripts/process_existing_resumes.py 0 23 24
python scripts/process_existing_resumes.py 0 34 35
```

---

## Cost Estimate

**Per Resume:**
- OpenAI API: ~$0.02-0.05
- Cloud Run: ~$0.001
- Pub/Sub: ~$0.0001
- **Total: ~$0.02-0.05 per resume**

**For 40 Resumes:**
- Total: ~$0.80-2.00
- Time: 40-60 minutes

---

## Best Practice Workflow

1. **Test First (5 resumes)**
   ```bash
   python scripts/process_existing_resumes.py 2 0 5
   ```

2. **Wait 5 minutes & verify** in Airtable
   - Check that 5 new applicants appeared
   - Spot-check 1-2 records for quality

3. **Process rest in batches of 10**
   ```bash
   python scripts/process_existing_resumes.py 2 5 15
   # Wait, verify
   python scripts/process_existing_resumes.py 2 15 25
   # Wait, verify
   python scripts/process_existing_resumes.py 2 25 40
   ```

4. **Final verification**
   - Check Airtable: Should have 40 new applicants
   - Check for any failed files in script output
   - Retry any failures

---

## Re-Running on Already Processed Resumes

**Q: What if I run this script twice?**

**A:** Each resume will be processed again, creating duplicate Airtable records.

**To avoid duplicates:**
1. Check Airtable before running
2. Note which resumes are already processed
3. Use start/end indexes to skip them

**Or:** Move processed resumes to a different folder

---

## Quick Reference

```bash
# Test with first 5
python scripts/process_existing_resumes.py 2 0 5

# Process all
python scripts/process_existing_resumes.py 2

# Process in batches of 10
python scripts/process_existing_resumes.py 2 0 10
python scripts/process_existing_resumes.py 2 10 20
python scripts/process_existing_resumes.py 2 20 30
python scripts/process_existing_resumes.py 2 30 40

# Monitor progress
gcloud logging tail "resource.labels.service_name=jetsmx-pubsub-handler" --project=jetsmx-agent

# Check Airtable
open https://airtable.com/<your-base>
```

