# Applicant Analysis Agent - Google ADK Implementation

## Overview

This is the Google ADK/Vertex AI Agent Builder implementation of the Applicant Analysis Agent, replacing the previous LangGraph-based approach. The agent processes resumes and generates applicant profiles for JetsMX hiring workflow.

## Architecture

### Tool-Based Pattern

The agent uses 7 specialized tools that execute the workflow:

1. **download_resume_from_drive** - Downloads PDF from Google Drive
2. **parse_resume_text** - Extracts structured data from PDF
3. **analyze_candidate_fit** - LLM-based suitability analysis
4. **create_applicant_records_in_airtable** - Creates Applicant and Pipeline records
5. **generate_icc_pdf** - Generates Initial Candidate Coverage report
6. **upload_icc_to_drive** - Uploads ICC and updates Applicant record
7. **publish_completion_event** - Publishes event to Pub/Sub

### Agent Reasoning

The Gemini 1.5 Pro model acts as the reasoning engine, deciding when and how to invoke tools based on the workflow requirements. This provides:

- **Flexibility**: Agent can adapt to edge cases
- **Error Recovery**: Can retry or take alternative paths
- **Scalability**: Vertex AI manages auto-scaling
- **Observability**: Built-in monitoring and tracing

## File Structure

```
agents/applicant_analysis/
├── README_ADK.md              # This file
├── agent_adk.py               # Main ADK agent definition
├── tools.py                   # All 7 tool definitions
├── models.py                  # Pydantic models for type safety
├── config.yaml                # Agent configuration
├── prompts.py                 # Existing prompts (reused)
├── resume_parser.py           # Existing parser (reused)
├── icc_generator.py           # Existing ICC generator (reused)
├── agent.py                   # Legacy LangGraph agent (deprecated)
└── graph.py                   # Legacy graph (deprecated)
```

## Usage

### Local Development

```python
from agents.applicant_analysis.agent_adk import process_resume

# Process a resume
result = process_resume(
    file_id="1AbCdEfGh...",
    filename="john_doe_resume.pdf"
)

if result['success']:
    print(f"Applicant ID: {result['applicant_id']}")
    print(f"Pipeline ID: {result['pipeline_id']}")
    print(f"ICC File ID: {result['icc_file_id']}")
    print(f"Verdict: {result['baseline_verdict']}")
else:
    print(f"Error: {result['error']}")
```

### From Pub/Sub Handler

```python
from infra.pubsub_handlers.handlers.drive_handler import handle_resume_upload

# Called automatically when resume uploaded to Drive
event_data = {
    'file_id': '1AbCdEfGh...',
    'name': 'john_doe_resume.pdf',
    'mime_type': 'application/pdf',
    'parents': ['folder_id...']
}

result = handle_resume_upload(event_data)
```

## Deployment

### Deploy to Vertex AI

```bash
python scripts/deploy_applicant_analysis_agent.py \
    --project jetsmx-prod \
    --location us-central1 \
    --staging-bucket gs://jetsmx-staging
```

### List Deployed Agents

```bash
python scripts/deploy_applicant_analysis_agent.py --list
```

### Delete Agent

```bash
python scripts/deploy_applicant_analysis_agent.py \
    --delete "projects/.../locations/.../reasoningEngines/..."
```

## Configuration

Edit `config.yaml` to customize:

- **Model settings**: temperature, max_tokens, top_p
- **System instruction**: Agent behavior and requirements
- **Agent executor**: max_iterations, early_stopping
- **Workflow settings**: timeouts, retries, logging

## Testing

### Run Unit Tests

```bash
pytest tests/unit/test_agents/test_applicant_analysis_tools.py -v
```

### Run Integration Tests

```bash
pytest tests/integration/test_applicant_analysis_agent_adk.py -v
```

### Run All Tests

```bash
pytest tests/ -k applicant_analysis -v
```

## Tool Descriptions

### 1. download_resume_from_drive

**Input**: `{"file_id": "string"}`

**Output**: 
```json
{
  "success": true,
  "pdf_content_base64": "JVBERi0xLjQK...",
  "file_size_bytes": 245632,
  "mime_type": "application/pdf",
  "error": null
}
```

### 2. parse_resume_text

**Input**: `{"pdf_content_base64": "string"}`

**Output**:
```json
{
  "success": true,
  "parsed_data": {
    "raw_text": "...",
    "email": "john@example.com",
    "phone": "(203) 555-1234",
    "has_faa_ap": true,
    "faa_ap_number": "1234567890",
    "years_in_aviation": 15,
    "business_aviation_experience": true,
    "aog_field_experience": true
  },
  "error": null
}
```

### 3. analyze_candidate_fit

**Input**: `{"parsed_resume_data": "json_string"}`

**Output**:
```json
{
  "success": true,
  "analysis": {
    "applicant_name": "John Doe",
    "aircraft_experience": "Gulfstream G450/G550, Citation CJ series",
    "engine_experience": "Honeywell TFE731, P&WC PT6A",
    "systems_strengths": "Avionics, Hydraulics, Powerplant",
    "aog_suitability_score": 8,
    "geographic_flexibility": "NE Corridor",
    "baseline_verdict": "Strong Fit",
    "missing_info": "Current employment status",
    "follow_up_questions": "What is your availability?"
  },
  "error": null
}
```

### 4. create_applicant_records_in_airtable

**Input**:
```json
{
  "parsed_data_json": "json_string",
  "analysis_json": "json_string",
  "resume_file_id": "string"
}
```

**Output**:
```json
{
  "success": true,
  "applicant_id": "recABC123",
  "pipeline_id": "recXYZ789",
  "error": null
}
```

### 5. generate_icc_pdf

**Input**:
```json
{
  "parsed_data_json": "json_string",
  "analysis_json": "json_string"
}
```

**Output**:
```json
{
  "success": true,
  "pdf_content_base64": "JVBERi0xLjQK...",
  "pdf_size_bytes": 45120,
  "error": null
}
```

### 6. upload_icc_to_drive

**Input**:
```json
{
  "pdf_content_base64": "string",
  "applicant_name": "string",
  "applicant_id": "string",
  "parent_folder_id": "string (optional)"
}
```

**Output**:
```json
{
  "success": true,
  "file_id": "1AbCdEfGh...",
  "web_view_link": "https://drive.google.com/file/d/.../view",
  "error": null
}
```

### 7. publish_completion_event

**Input**:
```json
{
  "applicant_id": "string",
  "pipeline_id": "string",
  "baseline_verdict": "string"
}
```

**Output**:
```json
{
  "success": true,
  "message_id": "123456789",
  "error": null
}
```

## Error Handling

All tools follow a consistent error handling pattern:

- **Return value**: Never raises exceptions, always returns dict
- **Success field**: Boolean indicating success/failure
- **Error field**: Detailed error message if failed, null if successful
- **Partial success**: Tools return as much data as possible even if some operations fail

## Monitoring

### View Agent Logs

```bash
gcloud logging read "resource.type=aiplatform.googleapis.com/ReasoningEngine" \
    --project=jetsmx-prod \
    --limit=50
```

### Agent Metrics

View in Google Cloud Console:
- Vertex AI → Reasoning Engines → applicant-analysis-agent
- Metrics: invocation count, latency, error rate

## Differences from LangGraph

| Aspect | LangGraph (Old) | Google ADK (New) |
|--------|-----------------|------------------|
| Orchestration | Explicit graph nodes/edges | Agent reasoning with tools |
| State | TypedDict passed through nodes | Agent context (implicit) |
| Control Flow | Hardcoded sequential edges | Agent decides tool order |
| Deployment | Custom Cloud Run service | Vertex AI managed service |
| Scaling | Manual container scaling | Auto-scaling by Vertex AI |
| Monitoring | Custom logging | Built-in Vertex AI metrics |
| Cost | Compute + LLM API calls | Managed service pricing |

## Troubleshooting

### Agent Not Using Tools

Check system instruction in `config.yaml` - ensure it explicitly instructs agent to use all tools sequentially.

### Tool Invocation Fails

1. Check tool function signature matches @tool decorator
2. Verify all parameters are serializable (no complex objects)
3. Check logs for specific error messages

### Deployment Fails

1. Ensure all dependencies are in requirements list
2. Verify GCP project and staging bucket are accessible
3. Check IAM permissions for Vertex AI service account

### Agent Returns Incomplete Results

Increase `max_iterations` in config.yaml if workflow is complex. Default is 15.

## Best Practices

1. **Tool Design**: Keep tools focused on single responsibility
2. **Error Messages**: Provide detailed, actionable error messages
3. **Logging**: Log at info level for workflow milestones, error level for failures
4. **Testing**: Test each tool independently before integration testing
5. **Monitoring**: Set up alerts for error rates and latency spikes

## Future Enhancements

- [ ] Add retry logic with exponential backoff for transient failures
- [ ] Implement circuit breaker pattern for external API calls
- [ ] Add caching for repeated analysis of similar resumes
- [ ] Support batch processing of multiple resumes
- [ ] Add streaming response for long-running workflows
- [ ] Implement human-in-the-loop approval before Airtable writes

## Support

For issues or questions:
- Check logs: `agents/applicant_analysis/*.log`
- Review audit trail in Airtable Interactions table
- Contact: Tyler @ JetsMX

