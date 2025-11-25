# Airtable Schema Setup Guide

This guide walks you through setting up your Airtable base structure from the YAML schema.

## Prerequisites

1. **Airtable Account** with API access
2. **Personal Access Token** (PAT) with schema write permissions
3. **Empty or new Base** created in Airtable UI

## Step 1: Create an Airtable Base

The Airtable API doesn't support creating bases programmatically, so you must create it manually:

1. Go to https://airtable.com
2. Click **"Create a base"** or **"Add a base"**
3. Select **"Start from scratch"**
4. Name it: `JetsMX Talent & Contractors` (or your preferred name)
5. Copy the **Base ID** from the URL: `https://airtable.com/{BASE_ID}`

## Step 2: Get Your API Token

1. Go to https://airtable.com/create/tokens
2. Click **"Create new token"**
3. Give it a name: `JetsMX Agent Schema Setup`
4. Add these scopes:
   - `schema.bases:read`
   - `schema.bases:write`
   - `data.records:read` (optional, for future use)
   - `data.records:write` (optional, for future use)
5. Add access to your base under "Access" section
6. Click **"Create token"**
7. Copy the token (it looks like `pat0WitBbTQxXDygm...`)

## Step 3: Configure Environment

Update your `.env` file:

```bash
# Replace with your actual values
AIRTABLE_API_KEY=pat0WitBbTQxXDygm.your_actual_token_here
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
```

## Step 4: Run the Setup Script

From the project root:

```bash
# Activate virtual environment if needed
source venv/bin/activate

# Run the setup script
python scripts/setup_airtable_schema.py
```

### Command Options

```bash
# Use base ID from .env (recommended)
python scripts/setup_airtable_schema.py

# Specify base ID explicitly
python scripts/setup_airtable_schema.py --base-id appXXXXXXXXXXXXXX

# Use custom schema file
python scripts/setup_airtable_schema.py --schema path/to/schema.yaml
```

## What the Script Does

### Pass 1: Create Tables with Basic Fields
Creates all 7 tables with these field types:
- Text fields (singleLineText, longText, email, phone, url)
- Number and checkbox fields
- Date/time fields (date, dateTime, createdTime, lastModifiedTime)
- Select fields (singleSelect, multipleSelect)

### Pass 2: Add Relationship Fields
Adds linking fields after all tables exist:
- `linkToAnotherRecord` - links between tables
- `lookup` - pulls data from linked tables (skipped, requires manual setup)

### Idempotency
The script is safe to run multiple times:
- Checks for existing tables before creating
- Skips tables that already exist
- Only creates missing tables/fields

## Expected Output

```
============================================================
Airtable Schema Setup
============================================================
Base ID: appXXXXXXXXXXXXXX
Schema: SCHEMA/airtable_schema.yaml
============================================================
Loading schema from SCHEMA/airtable_schema.yaml
Fetching existing tables from base appXXXXXXXXXXXXXX
Found 0 existing tables
Setting up schema with 7 tables

=== PASS 1: Creating tables with basic fields ===
Creating table 'Applicants'...
✓ Created table 'Applicants' (ID: tblXXXXXXXXXXXXXX) with 18 fields
Creating table 'Applicant Pipeline'...
✓ Created table 'Applicant Pipeline' (ID: tblYYYYYYYYYYYYYY) with 24 fields
...

=== PASS 2: Adding relationship fields ===
Processing relationships for 'Applicants'...
  Adding linkToAnotherRecord field 'Primary Aircraft Families' to 'Applicants'...
  ✓ Added field 'Primary Aircraft Families' (ID: fldZZZZZZZZZZZZZZ)
...

=== Schema setup complete ===
Created/verified 7 tables

Table Summary:
  • Applicants (ID: tblXXXXXXXXXXXXXX) - 22 fields
  • Applicant Pipeline (ID: tblYYYYYYYYYYYYYY) - 26 fields
  • Interactions (ID: tblAAAAAAAAAAAAA) - 7 fields
  • Contractors (ID: tblBBBBBBBBBBBBBB) - 19 fields
  • Aircraft Types (ID: tblCCCCCCCCCCCCCC) - 4 fields
  • Engine Families (ID: tblDDDDDDDDDDDDDD) - 3 fields
  • Airports (ID: tblEEEEEEEEEEEEEE) - 6 fields

✓ Setup completed successfully!

Your base is ready at: https://airtable.com/appXXXXXXXXXXXXXX
```

## Tables Created

The script creates these 7 tables:

1. **Applicants** - Master record for each job applicant
2. **Applicant Pipeline** - Funnel stages and automation triggers
3. **Interactions** - Chronological log of all applicant interactions
4. **Contractors** - Onboarded and approved technicians
5. **Aircraft Types** - Supported airframes and families
6. **Engine Families** - Engine types relevant to Jetstream work
7. **Airports** - Base and coverage airports for dispatch planning

## Known Limitations

### Lookup Fields
Lookup fields require the ID of a specific `linkToAnotherRecord` field in the same table. The script currently skips these with a warning. You'll need to configure lookup fields manually in the Airtable UI:

1. Go to the table
2. Add a field
3. Choose "Lookup"
4. Select the linked record field and the field to look up

### lastModifiedTime with Field Watching
The `lastModifiedTime` type with specific `watched_fields` configuration may need manual adjustment in the UI.

## Troubleshooting

### Error: "INVALID_PERMISSIONS_OR_MODEL_NOT_FOUND"
- Your API token doesn't have schema write permissions
- Recreate the token with `schema.bases:write` scope
- Make sure the token has access to your specific base

### Error: "TABLE_NOT_FOUND"
- Pass 2 relationship creation failed because a linked table doesn't exist
- Check the table names in your YAML match exactly
- Re-run the script (it's idempotent)

### Error: "AUTHENTICATION_REQUIRED"
- Your API key is invalid or expired
- Check the `AIRTABLE_API_KEY` in your `.env` file
- Generate a new Personal Access Token

### Script Fails Mid-Execution
- The script is idempotent - just re-run it
- Already created tables will be skipped
- New tables will be created

## Verification

After running the script:

1. Go to `https://airtable.com/{your_base_id}`
2. Verify all 7 tables are present
3. Click into each table and check fields
4. Verify relationships between tables work (linked record fields)

## Next Steps

After the base is set up:

1. **Populate Reference Tables**
   - Add aircraft types to `Aircraft Types` table
   - Add engine families to `Engine Families` table
   - Add airports to `Airports` table

2. **Test the Base**
   - Manually create a test applicant record
   - Verify all fields work as expected
   - Test linked record relationships

3. **Update Application Code**
   - Your Python code can now use the base via `tools/airtable/` modules
   - All table/field API names match the YAML schema

4. **Configure Automations**
   - Set up any Airtable automations you need
   - Configure views for different team members
   - Set up forms for data collection

