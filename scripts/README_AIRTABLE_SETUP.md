# Airtable Schema Setup Script

Automatically creates tables and fields in your Airtable base from the YAML schema definition.

## Prerequisites

1. **Create an Airtable base manually** (API doesn't support base creation)
   - Go to https://airtable.com
   - Create a new base named "JetsMX Talent & Contractors" (or any name)
   - Copy the base ID from the URL: `https://airtable.com/BASE_ID/...`

2. **Update your `.env` file**:
   ```bash
   AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX  # Replace with your actual base ID
   AIRTABLE_API_KEY=patXXXXXXXXXXXXXX  # Your personal access token
   ```

3. **Ensure dependencies are installed**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage (uses .env settings):
```bash
python scripts/setup_airtable_schema.py
```

### Specify a different base:
```bash
python scripts/setup_airtable_schema.py --base-id appYOURBASEID
```

### Use a different schema file:
```bash
python scripts/setup_airtable_schema.py --schema path/to/schema.yaml
```

## How It Works

The script uses a **two-pass approach** to handle field dependencies:

### Pass 1: Basic Fields
Creates all tables with basic field types:
- Text fields (singleLineText, longText, email, phoneNumber, url)
- Number fields
- Checkbox fields
- Select fields (singleSelect, multipleSelect)
- Date/time fields (date, dateTime, createdTime, lastModifiedTime)

### Pass 2: Relationships
Adds relationship fields after all tables exist:
- **linkToAnotherRecord** - Links between tables
- **lookup** - Look up values from linked records (may require manual setup)

## Idempotency

The script is **safe to run multiple times**:
- Checks for existing tables before creating
- Skips tables that already exist
- Only creates missing tables and fields
- Won't duplicate or overwrite existing data

## Output Example

```
Setting up Airtable base: appXXXXXXXXXXXXXX
Using schema: /path/to/SCHEMA/airtable_schema.yaml
Fetching existing tables from base appXXXXXXXXXXXXXX
Found 0 existing tables: []

=== PASS 1: Creating tables with basic fields ===
Creating table 'Applicants' with 19 basic fields
✓ Created table 'Applicants' (ID: tblXXXXXXXXXXXXXX)
Creating table 'Applicant Pipeline' with 23 basic fields
✓ Created table 'Applicant Pipeline' (ID: tblYYYYYYYYYYYYYY)
...

=== PASS 2: Adding relationship fields ===
Processing relationships for 'Applicants'
  Adding linkToAnotherRecord field 'Primary Aircraft Families' to 'Applicants'
  ✓ Added field 'Primary Aircraft Families'
...

=== Schema Setup Complete ===
Tables created/verified: 7

✓ Schema setup completed successfully!
```

## Troubleshooting

### Error: "AIRTABLE_API_KEY not found"
- Make sure you've created a `.env` file from `env.template`
- Add your Airtable Personal Access Token

### Error: "Base ID not provided"
- Set `AIRTABLE_BASE_ID` in `.env`
- Or use `--base-id` command line argument

### Error: "Please create an Airtable base"
- The Airtable API doesn't support creating bases programmatically
- You must create the base manually in the Airtable UI first

### Lookup fields show warnings
- Lookup fields are complex and may require manual configuration
- After the script runs, go to Airtable and manually add lookup fields
- The script will add all other field types automatically

### createdTime and lastModifiedTime fields
- These special system fields cannot be created via API
- They can only be added manually in the Airtable UI
- The script will skip them and log a note

## Schema File Format

The script reads `SCHEMA/airtable_schema.yaml`. Here's the structure:

```yaml
airtable_base:
  name: "Your Base Name"
  tables:
    - name: "Table Name"
      api_name: "table_api_name"
      description: "Table description"
      fields:
        - name: "Field Name"
          api_name: "field_api_name"
          type: "singleLineText"
          
        - name: "Status"
          type: "singleSelect"
          options: ["Option 1", "Option 2"]
          
        - name: "Related Records"
          type: "linkToAnotherRecord"
          link:
            table: "Other Table Name"
            relationship: "many"  # or "one", "zeroOrOne"
```

## Next Steps After Running

1. **Verify in Airtable**: Open your base and check all tables/fields were created
2. **Configure lookup fields**: Manually add any lookup fields that were skipped
3. **Set up views**: Create filtered/sorted views for your workflows
4. **Configure automations**: Set up any Airtable automations
5. **Test the integration**: Run `python scripts/test_workflows.py` to test

## API Rate Limits

The Airtable API has rate limits:
- 5 requests per second per base
- The script includes basic error handling but may fail on very large schemas
- If you hit rate limits, the script will show an error

## Support

For issues with:
- **The script**: Check logs and error messages
- **Airtable API**: See https://airtable.com/developers/web/api/introduction
- **Schema format**: Review `SCHEMA/airtable_schema.yaml`
