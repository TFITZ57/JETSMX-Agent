# JetsMX Agent Framework

Multi-agent system for JetstreamMX LLC, an AOG aircraft maintenance company operating in the U.S. Northeast.

## Overview

This framework implements automated workflows for HR/hiring processes using **pure Google ADK (Vertex AI with Gemini)** and Google Workspace APIs. No LangChain or LangGraph dependencies.

## Architecture

This is an **event-driven, multi-agent system** built with pure Google ADK (no LangChain/LangGraph).

### Core Components

- **Agents**: 3 specialized agents using Vertex AI with Gemini 1.5 Pro
  - Applicant Analysis Agent (resume processing)
  - Company Knowledge Base Agent (conversational Q&A)
  - HR Pipeline Agent (workflow orchestration)

- **Tools**: 33 pure Python functions across 6 API integrations
  - Airtable (10 tools): applicant/pipeline/contractor management
  - Gmail (6 tools): email drafts, sending, thread management
  - Calendar (4 tools): event creation, scheduling, availability
  - Drive (4 tools): file upload/download, metadata
  - Chat (4 tools): messages, approval cards, notifications
  - Pub/Sub (5 tools): event publishing for async workflows

- **Infrastructure**: Cloud Run microservices
  - Webhook receiver (Airtable, Gmail, Drive, Chat endpoints)
  - Pub/Sub handler (event routing and agent invocation)

- **Data Layer**: Airtable as source of truth
  - Applicants table
  - Applicant Pipeline table
  - Interactions table (audit log)
  - Contractors table

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Set up Google Cloud credentials**:
   - Place your service account key at `google-service-account-keys.json`
   - Ensure the service account has necessary IAM permissions

4. **Initialize Pub/Sub topics**:
   ```bash
   python scripts/setup_pubsub.py
   ```

5. **Set up Gmail watch**:
   ```bash
   python scripts/setup_gmail_watch.py
   ```

## Project Structure

```
agents/          # Agent graph definitions
tools/           # API client wrappers
infra/           # Cloud Run services (webhooks, Pub/Sub handlers)
shared/          # Shared utilities, models, config
SCHEMA/          # Data schemas and event routing
tests/           # Test suite
scripts/         # Utility scripts
docs/            # Documentation
```

## Workflows

### 1. Resume → Applicant Profile
New resume PDFs in Drive trigger analysis, ICC generation, and Airtable population.

### 2. Human Review & Initial Email
HR reviews applicants in Airtable, triggers automated outreach email drafts.

### 3. Parse Applicant Reply & Schedule Probe Call
Email replies are parsed, probe calls scheduled automatically.

### 4. Probe Call → Updated Profile
Transcripts analyzed, applicant profiles enriched.

### 5. Interview & Final Decision
Interview analysis, contractor onboarding preparation.

## Development

Run tests:
```bash
pytest tests/
```

Manual workflow testing:
```bash
python scripts/test_workflows.py
```

## Deployment

See `docs/deployment.md` for detailed deployment instructions.

## Documentation

- [Architecture](docs/architecture.md)
- [Workflows](docs/workflows.md)
- [API Usage](docs/api_usage.md)
- [Deployment](docs/deployment.md)

## Safety & Guardrails

All outbound communications and high-risk actions require human approval via Google Chat interactive cards.

