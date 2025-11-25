# JetsMX Agent Framework - Architecture Overview

## System Architecture

The JetsMX Agent Framework is a multi-agent system built on Google ADK, LangGraph, and Vertex AI Agent Builder for automating HR and hiring workflows.

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                    External Triggers                         │
│  Airtable │ Gmail │ Drive │ Google Chat │ Manual            │
└───────┬──────┬──────┬─────────┬──────────────────────────────┘
        │      │      │         │
        v      v      v         v
┌─────────────────────────────────────────────────────────────┐
│             Webhook Receiver (Cloud Run)                     │
│  FastAPI app receiving external webhooks                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        v
┌─────────────────────────────────────────────────────────────┐
│                   Pub/Sub Topics                             │
│  • jetsmx-airtable-events                                   │
│  • jetsmx-gmail-events                                      │
│  • jetsmx-drive-events                                      │
│  • jetsmx-chat-events                                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        v
┌─────────────────────────────────────────────────────────────┐
│          Pub/Sub Handler / Event Router (Cloud Run)         │
│  Routes events to appropriate agent workflows               │
└───────────┬───────────────┬──────────────┬──────────────────┘
            │               │              │
            v               v              v
┌───────────────┐  ┌────────────────┐  ┌───────────────────┐
│  Company KB   │  │   Applicant    │  │    HR Pipeline    │
│    Agent      │  │    Analysis    │  │      Agent        │
│               │  │     Agent      │  │                   │
│  (Vertex AI)  │  │  (Vertex AI)   │  │   (Vertex AI)     │
└───────┬───────┘  └───────┬────────┘  └────────┬──────────┘
        │                  │                     │
        └──────────────────┴─────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────┐
│                        Tools Layer                           │
│  Airtable │ Gmail │ Calendar │ Drive │ Chat │ Pub/Sub      │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Agents

#### Applicant Analysis Agent
- **Purpose**: Analyzes resumes, generates ICC reports, populates Airtable
- **Trigger**: Drive file upload (resume PDF)
- **Tools**: Drive, Airtable, Vertex AI (LLM)
- **Output**: Applicant record, Pipeline record, ICC PDF

**Workflow**:
1. Download resume PDF from Drive
2. Extract text and parse contact info, A&P license, experience
3. Use LLM to analyze fit for AOG work
4. Generate Initial Candidate Coverage (ICC) PDF
5. Create records in Airtable
6. Upload ICC to Drive

#### HR Pipeline Agent
- **Purpose**: Manages hiring workflow with human-in-the-loop
- **Triggers**: Airtable updates, Gmail replies, Chat commands
- **Tools**: Gmail, Calendar, Chat, Airtable
- **Human Approval**: All outbound emails via Chat cards

**Key Workflows**:
- Generate personalized outreach email drafts
- Parse applicant replies for availability
- Schedule probe calls and interviews
- Post approval cards to Chat
- Log all interactions in Airtable

#### Company KB Agent
- **Purpose**: Conversational query interface for company data
- **Trigger**: Manual Chat queries
- **Tools**: Read-only access to Airtable, Gmail, Calendar, Drive
- **Use Cases**: "How many applicants?", "Status of X?", "Find candidates with Y"

### 2. Tools Layer

Modular API wrappers for external services:

**Airtable Tools**:
- `airtable_create_applicant()`
- `airtable_update_pipeline()`
- `airtable_find_applicants()`
- `airtable_log_interaction()`

**Gmail Tools**:
- `gmail_create_draft()`
- `gmail_send_message()`
- `gmail_get_thread()`

**Calendar Tools**:
- `calendar_create_event()`
- `calendar_find_free_slots()`

**Drive Tools**:
- `drive_download_file()`
- `drive_upload_file()`
- `drive_list_files_in_folder()`

**Chat Tools**:
- `chat_post_approval_card()`
- `chat_post_notification()`

**Pub/Sub Tools**:
- `pubsub_publish_event()`

### 3. Infrastructure

#### Webhook Receiver (Cloud Run)
- **Port**: 8080
- **Endpoints**:
  - `/webhooks/airtable/applicant_pipeline`
  - `/webhooks/gmail`
  - `/webhooks/drive`
  - `/chat/command`
- **Function**: Receives webhooks, validates, publishes to Pub/Sub

#### Pub/Sub Handler (Cloud Run)
- **Port**: 8081
- **Endpoints**:
  - `/pubsub/airtable`
  - `/pubsub/gmail`
  - `/pubsub/drive`
  - `/pubsub/chat`
- **Function**: Consumes Pub/Sub messages, routes to agents

#### Event Router
- Loads routing rules from `event_routing.yaml`
- Maps events to agent workflows
- Handles conditional routing based on field values

### 4. Shared Utilities

**Configuration** (`shared/config/`):
- Environment-based settings via Pydantic
- Constants for table names, pipeline stages, etc.

**Logging** (`shared/logging/`):
- Structured JSON logging
- Audit trail for high-risk actions

**Auth** (`shared/auth/`):
- Google service account authentication
- Domain-wide delegation for Workspace APIs
- Webhook signature verification

**Models** (`shared/models/`):
- Pydantic models for data validation
- Type safety across the system

## Data Flow: Resume → Contractor

### 1. Resume Upload
- User uploads resume PDF to Drive folder
- Drive watch triggers webhook

### 2. Profile Generation
- Webhook → Pub/Sub → Applicant Analysis Agent
- Agent downloads, parses, analyzes resume
- Creates Applicant and Pipeline records
- Generates and uploads ICC PDF

### 3. Human Review
- HR reviews in Airtable interface
- Sets "Screening Decision" to "Approve"

### 4. Outreach
- Airtable webhook → Pub/Sub → HR Pipeline Agent
- Agent generates personalized email draft
- Posts approval card to Google Chat
- Human approves → Email sent

### 5. Scheduling
- Applicant replies with availability
- Gmail watch → Pub/Sub → HR Pipeline Agent
- Agent parses availability, suggests times
- Human confirms → Calendar event created with Meet link

### 6. Interview
- Probe call happens, transcript uploaded to Drive
- Drive webhook → Meeting Analysis Agent (future)
- Agent updates applicant profile with new info

### 7. Decision
- Final interview complete
- HR sets decision in Airtable
- Pipeline stage → "Ready for Contractor Onboarding"
- Contractor record created

## Security & Guardrails

### High-Risk Actions Requiring Approval
- Sending emails
- Creating calendar events
- Modifying critical Airtable fields

### Approval Pattern
1. Agent creates draft/plan
2. Posts interactive card to Chat
3. Human clicks "Approve"
4. Card interaction → Webhook → Agent completes action

### Audit Trail
All actions logged with:
- Timestamp
- Agent name
- User ID (if human-initiated)
- Resource type and ID
- Before/after state

## Deployment

### Cloud Run Services
- **jetsmx-webhooks**: Public endpoint for external webhooks
- **jetsmx-pubsub-handler**: Internal service for event processing

### Vertex AI Agents
- Deployed via Vertex AI Agent Builder
- Each agent has its own endpoint
- Managed scaling and monitoring

### Pub/Sub Topics
- `jetsmx-airtable-events`
- `jetsmx-gmail-events`
- `jetsmx-drive-events`
- `jetsmx-chat-events`

## Technology Stack

- **Language**: Python 3.11
- **Agent Framework**: LangGraph, Google ADK
- **LLM**: Gemini 1.5 Pro (Vertex AI)
- **APIs**: Google Workspace, Airtable
- **Infrastructure**: Cloud Run, Pub/Sub, Cloud Storage
- **Web Framework**: FastAPI
- **Data Validation**: Pydantic
- **Document Processing**: PyPDF2, pdfplumber, reportlab

## Future Enhancements

1. **Meeting Analysis Agent**: Automated transcript processing
2. **Contractor Management**: Track jobs, performance, availability
3. **QuickBooks Integration**: Automated invoicing and payments
4. **Advanced Scheduling**: Multi-participant availability optimization
5. **Analytics Dashboard**: Hiring funnel metrics and insights

