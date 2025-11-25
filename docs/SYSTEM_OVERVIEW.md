# JetsMX Agent Framework - Complete System Overview

**Generated:** November 25, 2025  
**Purpose:** Comprehensive architectural documentation for planning, refactoring, and expansion

---

## Table of Contents

1. [Tools & Functions](#1-tools--functions)
2. [Agents](#2-agents)
3. [Workflows](#3-workflows)
4. [Nodes](#4-nodes)
5. [Capabilities Map](#5-capabilities-map)
6. [Architecture Diagram](#6-architecture-diagram)
7. [Gaps & Recommendations](#7-gaps--recommendations)

---

## 1. Tools & Functions

### Overview
**Total Tools:** 39 LangGraph-wrapped tools + 7 ADK-specific tools = **46 total**

### 1.1 Airtable Tools (10 tools)
**Location:** `tools/airtable/tools.py`

| Tool Name | Purpose | Inputs | Outputs | Used By |
|-----------|---------|--------|---------|---------|
| `airtable_create_applicant` | Create new applicant record | applicant_data, initiated_by, reason | record_id | Applicant Analysis Agent, HR Pipeline Agent |
| `airtable_get_applicant` | Retrieve applicant by ID | record_id | applicant dict | Company KB Agent, HR Pipeline Agent |
| `airtable_update_applicant` | Update applicant record | record_id, updates, initiated_by, reason | bool | Applicant Analysis Agent, HR Pipeline Agent |
| `airtable_find_applicants` | Search applicants | formula (Airtable query) | list[applicant] | Company KB Agent |
| `airtable_create_pipeline` | Create pipeline record | applicant_id, stage, initiated_by, reason | record_id | Applicant Analysis Agent |
| `airtable_get_pipeline` | Retrieve pipeline by ID | record_id | pipeline dict | HR Pipeline Agent |
| `airtable_update_pipeline` | Update pipeline record | record_id, updates, initiated_by, reason | bool | HR Pipeline Agent |
| `airtable_find_pipeline_by_thread` | Find pipeline by Gmail thread | thread_id | pipeline dict | Gmail Router |
| `airtable_log_interaction` | Log applicant interaction | applicant_id, type, direction, channel, summary | record_id | All agents |
| `airtable_create_contractor` | Convert applicant to contractor | applicant_id, contractor_data | record_id | HR Pipeline Agent (future) |

**Dependencies:** `pyairtable`, `shared/models/applicant.py`, `shared/models/pipeline.py`

---

### 1.2 Gmail Tools (6 tools)
**Location:** `tools/gmail/tools.py`

| Tool Name | Purpose | Inputs | Outputs | Used By |
|-----------|---------|--------|---------|---------|
| `gmail_create_draft` | Create email draft | to, subject, body, thread_id? | draft_id, message_id, thread_id | HR Pipeline Agent |
| `gmail_send_draft` | Send existing draft | draft_id, initiated_by, reason, applicant_id? | message_id, thread_id | HR Pipeline Agent (approval workflow) |
| `gmail_send_message` | Send email directly | to, subject, body, initiated_by, reason, thread_id?, applicant_id? | message_id, thread_id | HR Pipeline Agent (rare use) |
| `gmail_get_message` | Retrieve message | message_id | message dict | Company KB Agent, Gmail Handler |
| `gmail_get_thread` | Retrieve entire thread | thread_id | thread dict with messages | HR Pipeline Agent, Company KB Agent |
| `gmail_list_threads` | Search threads | query?, max_results | list[thread] | Company KB Agent |

**Dependencies:** Google Workspace API, `tools/gmail/client.py`, audit logging
**Safety:** All send operations require `initiated_by` and `reason` parameters for audit trail

---

### 1.3 Calendar Tools (4 tools)
**Location:** `tools/calendar/tools.py`

| Tool Name | Purpose | Inputs | Outputs | Used By |
|-----------|---------|--------|---------|---------|
| `calendar_create_event` | Create calendar event + Meet link | summary, start_time, end_time, attendees?, description?, add_meet_link, applicant_id? | event_id, meet_link, html_link | HR Pipeline Agent |
| `calendar_get_event` | Retrieve event details | event_id | event dict | Company KB Agent |
| `calendar_list_events` | List events in time range | time_min?, time_max? | list[event] | Company KB Agent, HR Pipeline Agent |
| `calendar_find_free_slots` | Find available time slots | duration_minutes, search_window_days | list[{start, end}] | HR Pipeline Agent (scheduling) |

**Dependencies:** Google Calendar API, `tools/calendar/meet.py` for Meet link generation

---

### 1.4 Drive Tools (4 tools)
**Location:** `tools/drive/tools.py`

| Tool Name | Purpose | Inputs | Outputs | Used By |
|-----------|---------|--------|---------|---------|
| `drive_get_file_metadata` | Get file info | file_id | metadata dict | Company KB Agent, Drive Handler |
| `drive_download_file` | Download file content | file_id | bytes | Applicant Analysis Agent |
| `drive_upload_file` | Upload file to Drive | name, content, mime_type, parent_folder_id? | file_id | Applicant Analysis Agent (ICC upload) |
| `drive_list_files_in_folder` | List folder contents | folder_id, mime_type? | list[file metadata] | Company KB Agent |

**Dependencies:** Google Drive API, `tools/drive/client.py`

---

### 1.5 Chat Tools (4 tools)
**Location:** `tools/chat/tools.py`

| Tool Name | Purpose | Inputs | Outputs | Used By |
|-----------|---------|--------|---------|---------|
| `chat_post_message` | Post text message | text, thread_key? | message info | All agents (notifications) |
| `chat_post_approval_card` | Post interactive approval card | title, preview_text, approve_action_params, thread_key? | message info | HR Pipeline Agent (HITL approvals) |
| `chat_post_notification` | Post notification card | title, message, fields? | message info | All agents |
| `chat_post_applicant_summary` | Post applicant summary card | applicant_name, email, phone, has_ap, baseline_verdict | message info | Applicant Analysis Agent |

**Dependencies:** Google Chat API, `tools/chat/cards.py` for card builders
**Purpose:** Human-in-the-loop approvals and notifications

---

### 1.6 Pub/Sub Tools (5 tools)
**Location:** `tools/pubsub/tools.py`

| Tool Name | Purpose | Inputs | Outputs | Used By |
|-----------|---------|--------|---------|---------|
| `pubsub_publish_event` | Generic event publisher | topic_name, event_data, attributes? | message_id | All agents |
| `pubsub_publish_airtable` | Publish Airtable event | event_data | message_id | Airtable webhook receiver |
| `pubsub_publish_gmail` | Publish Gmail event | event_data | message_id | Gmail webhook receiver |
| `pubsub_publish_drive` | Publish Drive event | event_data | message_id | Drive webhook receiver |
| `pubsub_publish_chat` | Publish Chat event | event_data | message_id | Chat webhook receiver |

**Dependencies:** Google Cloud Pub/Sub, `tools/pubsub/publisher.py`

---

### 1.7 Applicant Analysis Tools (7 ADK-specific tools)
**Location:** `agents/applicant_analysis/tools.py`

| Tool Name | Purpose | Inputs | Outputs | Used By |
|-----------|---------|--------|---------|---------|
| `download_resume_from_drive` | Download PDF from Drive | file_id | {success, pdf_content_base64, file_size_bytes} | Applicant Analysis Agent (ADK) |
| `parse_resume_text` | Extract structured data from PDF | pdf_content_base64 | {success, parsed_data} | Applicant Analysis Agent (ADK) |
| `analyze_candidate_fit` | LLM-based suitability analysis | parsed_resume_data (JSON string) | {success, analysis} | Applicant Analysis Agent (ADK) |
| `create_applicant_records_in_airtable` | Create Applicant + Pipeline records | parsed_data_json, analysis_json, resume_file_id | {success, applicant_id, pipeline_id} | Applicant Analysis Agent (ADK) |
| `generate_icc_pdf` | Generate ICC report PDF | parsed_data_json, analysis_json | {success, pdf_content_base64, pdf_size_bytes} | Applicant Analysis Agent (ADK) |
| `upload_icc_to_drive` | Upload ICC and update Applicant | pdf_content_base64, applicant_name, applicant_id, parent_folder_id? | {success, file_id, web_view_link} | Applicant Analysis Agent (ADK) |
| `publish_completion_event` | Publish profile_created event | applicant_id, pipeline_id, baseline_verdict | {success, message_id} | Applicant Analysis Agent (ADK) |

**Dependencies:** `langchain_core.tools.tool` decorator, Gemini 1.5 Pro for analysis
**Return Pattern:** All tools return `{success: bool, error?: str, ...data}` for consistent error handling

---

### 1.8 Utility/Supporting Modules

| Module | Location | Purpose |
|--------|----------|---------|
| `resume_parser.py` | `agents/applicant_analysis/` | PDF text extraction, contact info parsing, A&P license detection |
| `icc_generator.py` | `agents/applicant_analysis/` | ICC PDF generation with reportlab |
| `parse_reply.py` | `agents/hr_pipeline/` | Parse applicant email replies for availability |
| `schedule_probe.py` | `agents/hr_pipeline/` | Schedule probe call with Calendar + Meet |
| `google_auth.py` | `shared/auth/` | Service account auth with domain-wide delegation |
| `webhook_auth.py` | `shared/auth/` | Webhook signature verification |
| `audit.py` | `shared/logging/` | Audit trail for high-risk actions |
| `constants.py` | `shared/config/` | Pipeline stages, table names, field mappings |

---

## 2. Agents

### 2.1 Applicant Analysis Agent (ADK Version) ⭐ PRIMARY

**File:** `agents/applicant_analysis/agent_adk.py`  
**Type:** Google ADK / Vertex AI Reasoning Engine Agent  
**Status:** ✅ Production-ready (pending deployment)

#### Role & Specialization
Autonomous resume processing agent that downloads PDFs from Drive, extracts structured data, analyzes candidate suitability for AOG technician roles, generates ICC reports, and populates Airtable.

#### Tools Available (7 specialized tools)
1. `download_resume_from_drive`
2. `parse_resume_text`
3. `analyze_candidate_fit`
4. `create_applicant_records_in_airtable`
5. `generate_icc_pdf`
6. `upload_icc_to_drive`
7. `publish_completion_event`

#### Input Schema
```python
{
  "file_id": str,      # Google Drive file ID
  "filename": str      # Original filename for reference
}
```

#### Output Schema
```python
{
  "success": bool,
  "applicant_id": str,          # Airtable record ID
  "pipeline_id": str,           # Airtable pipeline record ID
  "icc_file_id": str,          # Drive file ID of ICC PDF
  "applicant_name": str,
  "baseline_verdict": str,     # "Strong Fit" | "Maybe" | "Not a Fit" | "Needs More Info"
  "error": Optional[str]
}
```

#### Core Responsibilities
- Download and parse resume PDFs
- Extract: contact info, A&P license number, years of experience, aircraft/engine types
- Analyze fit using Gemini 1.5 Pro against JetsMX AOG requirements
- Generate professional ICC (Initial Candidate Coverage) PDF reports
- Create Applicant and Applicant Pipeline records in Airtable
- Upload ICC to Drive and link to Applicant record
- Publish completion events for downstream workflows
- Log all interactions for audit trail

#### When Invoked
**Trigger:** Drive file created event in "Resumes" folder (mime_type = "application/pdf")  
**Entry Point:** `process_resume(file_id, filename)` via Drive handler

#### Upstream Dependencies
- Drive webhook → Pub/Sub → Drive handler → Router
- Resume must be uploaded to monitored Drive folder

#### Downstream Dependencies
- Publishes `applicant_profile_created` event to `jetsmx-applicant-events` topic
- HR Pipeline Agent may be triggered if screening decision is auto-approved

#### System Instructions (excerpt)
```
You are the Applicant Analysis Agent for JetsMX, an AOG aviation maintenance company.

KEY REQUIREMENTS FOR JETSMX CANDIDATES:
- FAA A&P license (required)
- Business aviation experience (strongly preferred)
- AOG/field service experience (highly valuable)
- Mobile/on-call availability
- Geographic flexibility within NE corridor

WORKFLOW: Execute 7 steps sequentially, pass data between steps using JSON encoding.
```

#### Model Configuration
- **Model:** `gemini-1.5-pro`
- **Temperature:** 0.2 (deterministic, focused)
- **Max Output Tokens:** 8192
- **Top-P:** 0.95
- **Max Iterations:** 15

#### Memory Usage
- **Episodic:** Agent maintains state across workflow steps via intermediate results
- **Document:** Resume text + parsed data passed between tools
- **Vector:** None (future: semantic search of historical resumes)

#### Custom Nodes Used
None (uses Vertex AI Reasoning Engine orchestration, not LangGraph)

#### Related Prompts
- System instruction in `agent_adk.py`
- Analysis prompts in `prompts.py` (`SYSTEM_PROMPT`, `build_analysis_prompt`)

---

### 2.2 Applicant Analysis Agent (LangGraph Version) - LEGACY

**File:** `agents/applicant_analysis/graph.py`  
**Type:** LangGraph StateGraph  
**Status:** ⚠️ Preserved for rollback, superseded by ADK version

#### Workflow (5 nodes, linear)
1. **download_resume** → Downloads PDF from Drive
2. **parse_resume** → Extracts structured data
3. **analyze_with_llm** → LLM analysis of fit
4. **create_airtable_records** → Creates Applicant + Pipeline records
5. **generate_and_upload_icc** → Generates ICC PDF and uploads to Drive

#### State Schema
```python
class ApplicantAnalysisState(TypedDict):
    file_id: str
    filename: str
    pdf_content: bytes
    parsed_resume: dict
    llm_analysis: dict
    applicant_id: str
    pipeline_id: str
    icc_pdf_bytes: bytes
    icc_file_id: str
    error: str | None
```

#### Differences from ADK Version
- Uses LangGraph for explicit workflow orchestration (vs agent reasoning)
- Passes state object between nodes (vs tool parameter passing)
- Less flexible error recovery
- Requires manual graph compilation and deployment

---

### 2.3 HR Pipeline Agent

**File:** `agents/hr_pipeline/agent.py`  
**Type:** Procedural agent class (not LangGraph-based)  
**Status:** ✅ Active

#### Role & Specialization
Manages hiring workflow transitions with human-in-the-loop approvals for email outreach, reply parsing, and interview scheduling.

#### Tools Available
- All Gmail tools (create_draft, send_draft, get_message, get_thread)
- All Calendar tools (create_event, find_free_slots)
- All Chat tools (post_approval_card, post_notification)
- Airtable tools (get_pipeline, update_pipeline, log_interaction)
- Pub/Sub tools

#### Input/Output Schemas

**generate_outreach_draft:**
```python
Input: {"pipeline_id": str}
Output: {"success": bool, "draft_id": str, "pipeline_id": str}
```

**parse_applicant_email_reply:**
```python
Input: {
  "thread_id": str,
  "message_id": str,
  "body_text": str,
  "pipeline_id": str
}
Output: {
  "success": bool,
  "phone": str,
  "availability_windows": list[str],
  "proposed_times": list[dict],
  "constraints": str
}
```

**approve_probe_schedule:**
```python
Input: {
  "pipeline_id": str,
  "selected_time": {"start_time": str, "end_time": str},
  "phone_number": str?
}
Output: {
  "success": bool,
  "event_id": str,
  "meet_link": str
}
```

#### Core Responsibilities
1. **Outreach Generation:** Build personalized email drafts using templates
2. **Human Approval:** Post interactive Chat cards for email approval
3. **Reply Parsing:** Extract availability, phone number, constraints from applicant replies
4. **Scheduling:** Find free slots, propose times, create Calendar events with Meet links
5. **Pipeline Updates:** Track workflow stage progression in Airtable
6. **Interaction Logging:** Record all communications

#### When Invoked
**Triggers:**
- Airtable webhook: `Screening Decision = "Approve"` → `generate_outreach_draft()`
- Gmail webhook: Reply in known thread → `parse_applicant_email_reply()`
- Chat card interaction: Approve button click → `approve_probe_schedule()`
- Manual Chat command: `/probe <applicant_name>`

#### Upstream/Downstream Dependencies
- **Upstream:** Airtable webhook receiver, Gmail handler, Chat webhook
- **Downstream:** Gmail API (sends emails), Calendar API (creates events), Chat API (posts cards)

#### Memory Usage
- **Episodic:** None (stateless, triggered per event)
- **Document:** Accesses pipeline records from Airtable
- **Vector:** None

#### Related Prompts
- `prompts.py`: Email templates (`build_outreach_email`)
- `parse_reply.py`: NLP patterns for availability extraction

---

### 2.4 Company Knowledge Base Agent

**File:** `agents/company_kb/agent.py`  
**Type:** LangChain AgentExecutor with tool calling  
**Status:** ✅ Active

#### Role & Specialization
Read-only conversational interface for querying company data (applicants, contractors, emails, events) via natural language.

#### Tools Available (9 read-only tools)
- `airtable_get_applicant`
- `airtable_get_pipeline`
- `airtable_find_applicants`
- `gmail_get_message`
- `gmail_get_thread`
- `gmail_list_threads`
- `calendar_list_events`
- `drive_get_file_metadata`
- `drive_list_files_in_folder`

#### Input/Output Schema
```python
Input: {"question": str}  # Natural language query
Output: str               # Natural language answer
```

#### Core Responsibilities
- Answer questions about applicant status
- Search for candidates by criteria
- Retrieve email threads
- Check calendar availability
- Find documents in Drive
- Provide conversational responses

#### When Invoked
**Triggers:**
- Google Chat command: `/query <question>`
- Manual invocation via API
- Future: Integrated into Chat bot

#### Example Queries
- "How many applicants do we have in the pipeline?"
- "Show me applicants with A&P licenses in the Northeast"
- "What's the status of John Smith's application?"
- "Find emails from last week about interviews"

#### System Instruction (excerpt)
```
You are the Company Knowledge Base Agent for JetsMX.
You have read-only access to applicant data, emails, calendar, and Drive files.
Answer questions conversationally using available tools.
If you don't have access to specific data, say so clearly.
```

#### Model Configuration
- **Model:** `gemini-1.5-pro`
- **Temperature:** 0.7 (more creative for natural responses)
- **Max Iterations:** 10
- **Handle Parsing Errors:** True

#### Memory Usage
- **Episodic:** Conversation history maintained within session
- **Document:** None
- **Vector:** None (future: semantic search)

---

### 2.5 Master Coordinator / Orchestrator

**Status:** ⚠️ Not implemented as separate agent

**Current Approach:** Event routing via `infra/pubsub_handlers/router.py`

The router acts as a lightweight orchestrator that:
- Receives events from Pub/Sub topics
- Applies routing rules from `SCHEMA/event_routing.yaml`
- Invokes appropriate agent methods
- Returns results to Pub/Sub or webhooks

**Future Enhancement:** Could be implemented as a full LangGraph orchestrator agent with:
- Multi-agent coordination
- Workflow state management
- Conditional branching across agents
- Error recovery and retries

---

## 3. Workflows

### 3.1 Resume → Applicant Profile (ADK Version - PRIMARY)

**Workflow Name:** `applicant_analysis_adk_workflow`  
**File Location:** `agents/applicant_analysis/agent_adk.py`  
**Trigger:** Drive file upload (PDF in "Resumes" folder)

#### Step-by-Step Flow

```
1. DOWNLOAD RESUME
   Tool: download_resume_from_drive(file_id)
   Input: file_id
   Output: {success, pdf_content_base64, file_size_bytes}
   
   ↓

2. PARSE RESUME TEXT
   Tool: parse_resume_text(pdf_content_base64)
   Input: Base64-encoded PDF from step 1
   Output: {success, parsed_data: {email, phone, location, has_faa_ap, faa_ap_number, ...}}
   
   ↓

3. ANALYZE CANDIDATE FIT
   Tool: analyze_candidate_fit(json.dumps(parsed_data))
   Input: JSON string of parsed_data from step 2
   LLM: Gemini 1.5 Pro analyzes against AOG requirements
   Output: {success, analysis: {applicant_name, baseline_verdict, aog_suitability_score, ...}}
   
   ↓

4. CREATE AIRTABLE RECORDS
   Tool: create_applicant_records_in_airtable(parsed_data_json, analysis_json, resume_file_id)
   Input: Data from steps 2 & 3, plus original file_id
   Creates: Applicant record + Applicant Pipeline record
   Logs: Interaction record
   Output: {success, applicant_id, pipeline_id}
   
   ↓

5. GENERATE ICC PDF
   Tool: generate_icc_pdf(parsed_data_json, analysis_json)
   Input: Data from steps 2 & 3
   Generates: Professional PDF report with assessment
   Output: {success, pdf_content_base64, pdf_size_bytes}
   
   ↓

6. UPLOAD ICC TO DRIVE
   Tool: upload_icc_to_drive(pdf_content_base64, applicant_name, applicant_id)
   Input: PDF from step 5, applicant info from steps 3 & 4
   Uploads: ICC to Drive
   Updates: Applicant record with ICC file reference
   Output: {success, file_id, web_view_link}
   
   ↓

7. PUBLISH COMPLETION EVENT
   Tool: publish_completion_event(applicant_id, pipeline_id, baseline_verdict)
   Input: IDs from step 4, verdict from step 3
   Publishes: Event to jetsmx-applicant-events topic
   Output: {success, message_id}
```

#### Conditional Branches
- If any step fails, agent logs error but continues to next step where possible
- Agent can skip steps if dependencies are missing (e.g., skip ICC upload if generation failed)
- LLM reasoning determines whether to retry failed tools

#### Async/Batched Operations
- None (sequential execution)
- Future: Batch processing of multiple resumes

#### Tools by Stage
- **Download:** drive_download_file
- **Parse:** pdfplumber, PyPDF2, regex patterns
- **Analyze:** Gemini 1.5 Pro via ChatVertexAI
- **Store:** Airtable API
- **Generate:** reportlab PDF generation
- **Upload:** Drive API
- **Publish:** Pub/Sub

#### Data Movement
```
Drive → bytes → base64 → parsed_dict → JSON string → LLM → analysis_dict → 
JSON string → Airtable → record_ids → ICC PDF bytes → base64 → Drive → Pub/Sub
```

---

### 3.2 Resume → Applicant Profile (LangGraph Version - LEGACY)

**Workflow Name:** `applicant_analysis_graph`  
**File Location:** `agents/applicant_analysis/graph.py`  
**Status:** Preserved for rollback

#### Node Sequence
```
START → download_resume_node → parse_resume_node → analyze_with_llm_node → 
create_airtable_records_node → generate_and_upload_icc_node → END
```

#### Key Differences from ADK Version
- Explicit graph structure (no agent reasoning)
- State object passed between nodes
- Less flexible error handling
- No tool-level granularity

---

### 3.3 HR Outreach Workflow

**Workflow Name:** `hr_outreach_workflow`  
**Trigger:** Airtable webhook - `Screening Decision = "Approve"`

#### Flow
```
1. AIRTABLE WEBHOOK
   Event: {table_id: "applicant_pipeline", changed_fields: ["Screening Decision"], new_values: {screening_decision: "Approve"}}
   
   ↓

2. PUB/SUB PUBLISH
   Webhook receiver → jetsmx-airtable-events topic
   
   ↓

3. EVENT ROUTER
   router.route_airtable_event() → Checks routing rules
   
   ↓

4. HR AGENT INVOCATION
   hr_agent.generate_outreach_draft(pipeline_id)
   
   ↓

5. BUILD EMAIL
   Uses prompts.build_outreach_email(applicant_name, aircraft_types)
   Generates personalized email with company intro, job description
   
   ↓

6. CREATE GMAIL DRAFT
   gmail.create_draft_message(to, subject, body)
   Stores draft in Gmail (NOT sent)
   
   ↓

7. UPDATE PIPELINE
   airtable.update_pipeline(pipeline_id, {outreach_email_draft_id, email_draft_generated: True, pipeline_stage: "Outreach Draft Created"})
   
   ↓

8. POST APPROVAL CARD TO CHAT
   chat.post_approval_card(title, preview_text, approve_action_params)
   Human sees email preview in Chat with Approve/Reject buttons
   
   ↓

9. HUMAN APPROVAL (async)
   User clicks "Approve" → Chat webhook → /chat/interaction endpoint
   
   ↓

10. SEND EMAIL
    router.route_chat_event() → gmail.send_draft(draft_id)
    Email sent to applicant
    Pipeline updated to "Outreach Sent"
    Interaction logged
```

---

### 3.4 Email Reply Parsing & Scheduling Workflow

**Trigger:** Gmail push notification (reply in known thread)

#### Flow
```
1. GMAIL PUSH NOTIFICATION
   Gmail watch → POST /webhooks/gmail
   
   ↓

2. WEBHOOK RECEIVER
   Extracts history_id → Fetches new messages from Gmail API
   
   ↓

3. PUB/SUB PUBLISH
   Publishes to jetsmx-gmail-events topic
   
   ↓

4. GMAIL HANDLER
   handlers/gmail_handler.py → handle_gmail_event()
   Retrieves full message and thread
   
   ↓

5. FIND PIPELINE
   airtable.find_pipeline_by_thread_id(thread_id)
   Links reply to applicant
   
   ↓

6. PARSE REPLY
   hr_agent.parse_applicant_email_reply(thread_id, message_id, body_text, pipeline_id)
   
   ↓

7. EXTRACT AVAILABILITY
   parse_reply.parse_applicant_reply(body_text)
   Uses regex + NLP to extract:
   - Phone number
   - Availability windows ("Monday afternoons", "weekdays after 3pm")
   - Constraints ("not available Thursdays")
   - Proposed specific times
   
   ↓

8. FIND FREE SLOTS
   calendar.find_free_slots(duration_minutes=30, search_window_days=7)
   Cross-references applicant availability with company calendar
   
   ↓

9. UPDATE PIPELINE
   airtable.update_pipeline(pipeline_id, {
     last_reply_received_at,
     last_reply_summary,
     confirmed_phone_number,
     preferred_call_window_1,
     preferred_call_window_2,
     pipeline_stage: "Applicant Responded"
   })
   
   ↓

10. POST SCHEDULING CARD
    chat.post_probe_scheduling_card(applicant_name, email_summary, proposed_times, pipeline_id)
    Human sees proposed times and can select one
    
    ↓

11. HUMAN SELECTS TIME (async)
    User clicks time slot → Chat webhook
    
    ↓

12. CREATE CALENDAR EVENT
    hr_agent.approve_probe_schedule(pipeline_id, selected_time, phone_number)
    calendar.create_event(summary, start_time, end_time, attendees, add_meet_link=True)
    Creates event with Google Meet link
    
    ↓

13. SEND CONFIRMATION EMAIL
    gmail.create_draft() or gmail.send_message() with event details
    
    ↓

14. UPDATE PIPELINE
    Pipeline stage → "Probe Call Scheduled"
    Log interaction
```

---

### 3.5 Event Routing Workflow (Meta-Workflow)

**File:** `infra/pubsub_handlers/router.py`  
**Purpose:** Routes all incoming events to appropriate agents

#### Event Sources & Routing

```
┌─────────────────────────────────────────────────────────┐
│  EXTERNAL EVENT SOURCES                                  │
├─────────────────────────────────────────────────────────┤
│  • Airtable Webhooks                                    │
│  • Gmail Push Notifications                             │
│  • Drive Push Notifications                             │
│  • Google Chat Commands                                 │
│  • Manual API Calls                                     │
└─────────────────────────┬───────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────┐
│  WEBHOOK RECEIVER (Cloud Run)                           │
│  infra/webhooks/main.py                                 │
│                                                          │
│  Routes:                                                │
│  • POST /webhooks/airtable/applicant_pipeline           │
│  • POST /webhooks/gmail                                 │
│  • POST /webhooks/drive                                 │
│  • POST /chat/command                                   │
│  • POST /chat/interaction                               │
└─────────────────────────┬───────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────┐
│  PUB/SUB TOPICS                                         │
│  • jetsmx-airtable-events                               │
│  • jetsmx-gmail-events                                  │
│  • jetsmx-drive-events                                  │
│  • jetsmx-chat-events                                   │
│  • jetsmx-applicant-events (agent-generated)            │
└─────────────────────────┬───────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────┐
│  PUB/SUB HANDLER (Cloud Run)                            │
│  infra/pubsub_handlers/main.py                          │
│                                                          │
│  Endpoints:                                             │
│  • POST /pubsub/airtable                                │
│  • POST /pubsub/gmail                                   │
│  • POST /pubsub/drive                                   │
│  • POST /pubsub/chat                                    │
└─────────────────────────┬───────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────┐
│  EVENT ROUTER                                           │
│  infra/pubsub_handlers/router.py                        │
│                                                          │
│  route_event(event_name, event_data)                    │
│    ├─ route_airtable_event()                            │
│    ├─ route_gmail_event()                               │
│    ├─ route_drive_event()                               │
│    └─ route_chat_event()                                │
└─────────────────────────┬───────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────┐
│  SPECIALIZED HANDLERS                                   │
│  • handlers/drive_handler.py                            │
│  • handlers/gmail_handler.py                            │
│  • (future: airtable_handler.py, chat_handler.py)      │
└─────────────────────────┬───────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────┐
│  AGENT INVOCATION                                       │
│  • Applicant Analysis Agent (ADK)                       │
│  • HR Pipeline Agent                                    │
│  • Company KB Agent                                     │
└─────────────────────────────────────────────────────────┘
```

#### Routing Rules (from event_routing.yaml)

**Airtable Events:**
- `Screening Decision = "Approve"` → HR Pipeline: generate_outreach_draft
- `Pipeline Stage = "Interview Complete"` → HR Pipeline: post_interview_decision_prompt
- `Background Check Status = "Passed"` → HR Pipeline: create_contractor_record

**Gmail Events:**
- Reply in known thread → HR Pipeline: parse_applicant_email_reply

**Drive Events:**
- PDF in "Resumes" folder → Applicant Analysis Agent: process_resume
- Transcript in "Transcripts - Probe Calls" → Meeting Analysis Agent (future)
- Transcript in "Transcripts - Interviews" → Meeting Analysis Agent (future)

**Chat Events:**
- `/probe` command → HR Pipeline: schedule_probe_call
- `/interview` command → HR Pipeline: schedule_interview
- `/applicant` command → Company KB: lookup_applicant_profile
- Approval card click → Execute approved action

---

## 4. Nodes

### 4.1 LangGraph Nodes (Legacy Applicant Analysis)

**File:** `agents/applicant_analysis/graph.py`

| Node Name | Type | Purpose | Inputs | Outputs |
|-----------|------|---------|--------|---------|
| `download_resume_node` | Transform | Downloads PDF from Drive | state.file_id | state.pdf_content |
| `parse_resume_node` | Transform | Extracts structured data | state.pdf_content | state.parsed_resume |
| `analyze_with_llm_node` | LLM | Analyzes candidate fit | state.parsed_resume | state.llm_analysis |
| `create_airtable_records_node` | Tool | Creates Applicant + Pipeline | state.parsed_resume, state.llm_analysis | state.applicant_id, state.pipeline_id |
| `generate_and_upload_icc_node` | Tool + Transform | Generates PDF and uploads | state.parsed_resume, state.llm_analysis, state.applicant_id | state.icc_file_id |

**Graph Structure:**
```python
workflow.set_entry_point("download_resume")
workflow.add_edge("download_resume", "parse_resume")
workflow.add_edge("parse_resume", "analyze_with_llm")
workflow.add_edge("analyze_with_llm", "create_airtable_records")
workflow.add_edge("create_airtable_records", "generate_and_upload_icc")
workflow.add_edge("generate_and_upload_icc", END)
```

---

### 4.2 ADK Tool Nodes (Current Implementation)

**File:** `agents/applicant_analysis/tools.py`

The ADK version doesn't use explicit graph nodes. Instead, Gemini 1.5 Pro acts as the reasoning engine and decides when to invoke each tool. The 7 tools effectively become "virtual nodes" in an agent-orchestrated workflow.

| Tool (Virtual Node) | Type | Purpose |
|---------------------|------|---------|
| `download_resume_from_drive` | Tool/IO | Fetches PDF bytes from Drive |
| `parse_resume_text` | Tool/Transform | PDF → structured dict |
| `analyze_candidate_fit` | Tool/LLM | LLM reasoning about suitability |
| `create_applicant_records_in_airtable` | Tool/IO | Writes to Airtable |
| `generate_icc_pdf` | Tool/Transform | dict → PDF bytes |
| `upload_icc_to_drive` | Tool/IO | Uploads PDF to Drive |
| `publish_completion_event` | Tool/IO | Publishes to Pub/Sub |

---

### 4.3 Router Nodes

**File:** `infra/pubsub_handlers/router.py`

| Node Name | Type | Purpose |
|-----------|------|---------|
| `route_event` | Router | Main routing function, dispatches by event type |
| `route_airtable_event` | Router | Routes Airtable webhooks based on table + field changes |
| `route_gmail_event` | Router | Routes Gmail notifications to gmail_handler |
| `route_drive_event` | Router | Routes Drive notifications to drive_handler |
| `route_chat_event` | Router | Routes Chat commands/interactions to appropriate actions |

**Routing Logic:**
- Loads rules from `SCHEMA/event_routing.yaml`
- Applies conditional logic (e.g., field value checks)
- Invokes agent methods directly
- Returns result to Pub/Sub or webhook caller

---

### 4.4 Specialized Handler Nodes

**File:** `infra/pubsub_handlers/handlers/`

| Handler | Purpose | Key Functions |
|---------|---------|---------------|
| `drive_handler.py` | Processes Drive events | `handle_drive_event()`, `handle_resume_upload()` |
| `gmail_handler.py` | Processes Gmail events | `handle_gmail_event()`, fetch full message from history_id |

These handlers act as preprocessing nodes before agent invocation:
- Fetch additional context (e.g., full message from history_id)
- Determine which agent to invoke
- Format data into agent input schema
- Handle errors and logging

---

### 4.5 Node Type Summary

| Node Type | Count | Purpose | Examples |
|-----------|-------|---------|----------|
| **Transform** | 3 | Data transformation without external calls | parse_resume_node, parse_reply |
| **Tool/IO** | 30+ | External API calls (Airtable, Gmail, Drive, etc.) | All tools in tools/ |
| **LLM** | 2 | LLM reasoning/analysis | analyze_with_llm_node, analyze_candidate_fit tool |
| **Router** | 5 | Conditional routing based on event data | route_event, route_airtable_event, etc. |
| **Handler** | 2 | Preprocessing + context fetching | drive_handler, gmail_handler |
| **Memory Retrieval** | 0 | (Future: vector search, episodic memory) | - |
| **Safety/Validation** | 0 | (Future: content moderation, PII detection) | - |
| **Retry** | 0 | (Future: exponential backoff, circuit breaker) | - |

---

## 5. Capabilities Map

### 5.1 Top-Level Capabilities Inventory

#### CRM / HubSpot
- ❌ **Not Implemented** (planned for future)
- Would mirror Airtable functionality

#### Airtable (Current CRM)
✅ **Fully Implemented**
- Create/Read/Update applicants
- Create/Read/Update pipeline records
- Log interactions
- Find applicants by query
- Create contractors
- Link records across tables

#### Google Workspace

**Gmail:**
✅ **Fully Implemented**
- Create drafts
- Send drafts (with approval)
- Send messages (with approval)
- Get messages/threads
- List threads by query
- Watch for push notifications

**Drive:**
✅ **Fully Implemented**
- Download files
- Upload files
- Get file metadata
- List folder contents
- Watch folders for changes

**Calendar:**
✅ **Fully Implemented**
- Create events with Google Meet
- Get event details
- List events
- Find free/busy slots

**Chat:**
✅ **Fully Implemented**
- Post text messages
- Post interactive approval cards
- Post notification cards
- Post applicant summary cards
- Handle card interactions (button clicks)

#### QuickBooks
- ❌ **Not Implemented** (planned for future)
- Would support: invoicing, time tracking, payment recording

#### DocuSign
- ❌ **Not Implemented** (planned for future)
- Would support: send contracts for signature, track status

#### Data Analysis
⚠️ **Partially Implemented**
- Resume parsing (structured extraction)
- Candidate suitability analysis
- Email reply parsing (availability extraction)
- Missing: analytics dashboard, reporting, trend analysis

#### Document Generation
✅ **Implemented**
- ICC PDF generation (resume summaries)
- Email template generation
- Missing: contract generation, offer letters

#### Scheduling & Dispatch Workflows
✅ **Implemented**
- Probe call scheduling with Meet links
- Availability matching
- Calendar integration
- Missing: multi-technician dispatch, job scheduling

#### HR / Resume Parsing
✅ **Fully Implemented**
- PDF text extraction
- Contact info extraction
- A&P license detection
- Experience summarization
- LLM-based fit analysis

#### Applicant Pipeline
✅ **Fully Implemented**
- Automated profile creation
- Stage tracking
- Human-in-the-loop approvals
- Email outreach
- Reply parsing
- Interview scheduling
- Missing: background check integration, offer management

#### Website / HubSpot Forms
- ❌ **Not Implemented**
- Would capture: applicant submissions, contact forms

#### Business Intelligence
⚠️ **Basic Implementation**
- Company KB Agent (conversational queries)
- Airtable data access
- Missing: dashboards, metrics, predictive analytics

#### Aviation / AOG-Specific
✅ **Implemented**
- A&P license validation
- AOG experience assessment
- Aircraft type matching
- Business aviation focus
- Geographic flexibility checks
- Missing: FAA database integration, aircraft-specific workflows

#### Tooling for Troubleshooting, Logging, Debugging
✅ **Fully Implemented**
- Structured JSON logging (`shared/logging/logger.py`)
- Audit trail for high-risk actions (`shared/logging/audit.py`)
- Interaction logging in Airtable
- Cloud Run logs
- Pub/Sub message tracking
- Missing: Error dashboards, alerting, APM

---

### 5.2 Capabilities → Agent → Workflow → Tools Mapping

#### Resume Processing
**Capability:** Automated resume → applicant profile  
**Agent:** Applicant Analysis Agent (ADK)  
**Workflow:** applicant_analysis_adk_workflow  
**Tools:**
- download_resume_from_drive
- parse_resume_text
- analyze_candidate_fit (Gemini 1.5 Pro)
- create_applicant_records_in_airtable
- generate_icc_pdf
- upload_icc_to_drive
- publish_completion_event

---

#### Email Outreach
**Capability:** Generate personalized outreach emails  
**Agent:** HR Pipeline Agent  
**Workflow:** hr_outreach_workflow  
**Tools:**
- airtable_get_pipeline
- gmail_create_draft
- airtable_update_pipeline
- chat_post_approval_card
- airtable_log_interaction

---

#### Reply Processing
**Capability:** Parse applicant email replies for availability  
**Agent:** HR Pipeline Agent  
**Workflow:** email_reply_parsing_workflow  
**Tools:**
- gmail_get_thread
- airtable_find_pipeline_by_thread
- airtable_update_pipeline
- chat_post_notification

**Supporting Module:** `agents/hr_pipeline/parse_reply.py`

---

#### Interview Scheduling
**Capability:** Schedule probe calls/interviews with Meet links  
**Agent:** HR Pipeline Agent  
**Workflow:** scheduling_workflow  
**Tools:**
- calendar_find_free_slots
- calendar_create_event
- gmail_create_draft (or send_message)
- airtable_update_pipeline
- chat_post_notification

**Supporting Module:** `agents/hr_pipeline/schedule_probe.py`

---

#### Conversational Data Access
**Capability:** Natural language queries about applicants/pipeline  
**Agent:** Company KB Agent  
**Workflow:** conversational_query_workflow  
**Tools:**
- airtable_get_applicant
- airtable_find_applicants
- airtable_get_pipeline
- gmail_list_threads
- calendar_list_events
- drive_list_files_in_folder

---

#### Audit & Compliance
**Capability:** Track all system actions with audit trail  
**Agent:** All agents  
**Workflow:** Logging in every workflow  
**Tools:**
- airtable_log_interaction
- audit.py logging
- All tools with `initiated_by` and `reason` parameters

---

#### Event-Driven Orchestration
**Capability:** React to external events (webhooks, file uploads)  
**Agent:** Event Router  
**Workflow:** event_routing_workflow  
**Tools:**
- pubsub_publish_* (all variants)
- Route handlers

**Supporting Files:**
- `infra/webhooks/main.py`
- `infra/pubsub_handlers/router.py`
- `SCHEMA/event_routing.yaml`

---

## 6. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL TRIGGER LAYER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Airtable │  │  Gmail   │  │  Drive   │  │   Chat   │  │  Manual  │     │
│  │ Webhooks │  │   Push   │  │   Push   │  │ Commands │  │API Calls │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │             │             │             │             │              │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────────┘
        │             │             │             │             │
        v             v             v             v             v
┌─────────────────────────────────────────────────────────────────────────────┐
│                    WEBHOOK RECEIVER (Cloud Run - Port 8080)                  │
│                        infra/webhooks/main.py (FastAPI)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Endpoints:                                                                  │
│  • POST /webhooks/airtable/applicant_pipeline                                │
│  • POST /webhooks/gmail                                                      │
│  • POST /webhooks/drive                                                      │
│  • POST /chat/command                                                        │
│  • POST /chat/interaction                                                    │
│                                                                               │
│  Functions:                                                                  │
│  • Validate webhook signatures                                               │
│  • Parse payloads                                                            │
│  • Publish to Pub/Sub topics                                                 │
│  • Return 200 OK immediately                                                 │
│                                                                               │
└───────┬────────────┬─────────────┬─────────────┬────────────────────────────┘
        │            │             │             │
        v            v             v             v
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PUB/SUB TOPICS (GCP)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌────────────────────┐  │
│  │jetsmx-airtable-     │  │jetsmx-gmail-        │  │jetsmx-drive-       │  │
│  │       events         │  │      events         │  │     events         │  │
│  └──────────┬───────────┘  └──────────┬──────────┘  └─────────┬──────────┘  │
│             │                         │                        │             │
│  ┌──────────▼──────────┐  ┌───────────▼─────────┐  ┌──────────▼─────────┐  │
│  │jetsmx-chat-         │  │jetsmx-applicant-    │  │    (future:        │  │
│  │      events         │  │      events         │  │  more topics)      │  │
│  └──────────┬───────────┘  └─────────────────────┘  └────────────────────┘  │
│             │                                                                 │
└─────────────┼──────────────────────────────────────────────────────────────┘
              │
              v
┌─────────────────────────────────────────────────────────────────────────────┐
│                   PUB/SUB HANDLER (Cloud Run - Port 8081)                    │
│                   infra/pubsub_handlers/main.py (FastAPI)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Endpoints:                                                                  │
│  • POST /pubsub/airtable                                                     │
│  • POST /pubsub/gmail                                                        │
│  • POST /pubsub/drive                                                        │
│  • POST /pubsub/chat                                                         │
│                                                                               │
│  Functions:                                                                  │
│  • Decode base64 Pub/Sub messages                                            │
│  • Extract event data                                                        │
│  • Route to event router                                                     │
│                                                                               │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                v
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EVENT ROUTER & HANDLERS                               │
│                   infra/pubsub_handlers/router.py                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ route_event(event_name, event_data)                                   │  │
│  │   ├─ route_airtable_event() ──> Check field changes, invoke agents   │  │
│  │   ├─ route_gmail_event() ──────> gmail_handler.handle_gmail_event()  │  │
│  │   ├─ route_drive_event() ──────> drive_handler.handle_drive_event()  │  │
│  │   └─ route_chat_event() ───────> Parse commands, invoke agents       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  Routing Rules: SCHEMA/event_routing.yaml                                    │
│  Specialized Handlers:                                                       │
│  • handlers/drive_handler.py ───> handle_resume_upload()                     │
│  • handlers/gmail_handler.py ───> Fetch full message from history_id         │
│                                                                               │
└────────┬────────────┬──────────────┬──────────────────────────────────────┘
         │            │              │
         v            v              v
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AGENT LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────────────┐  ┌─────────────────────┐  ┌─────────────────┐  │
│  │ Applicant Analysis     │  │   HR Pipeline       │  │   Company KB    │  │
│  │      Agent (ADK)       │  │       Agent         │  │      Agent      │  │
│  │                        │  │                     │  │                 │  │
│  │ File: agent_adk.py     │  │ File: agent.py      │  │ File: agent.py  │  │
│  │ Type: Vertex AI        │  │ Type: Procedural    │  │ Type: LangChain │  │
│  │       Reasoning Engine │  │       Class         │  │  AgentExecutor  │  │
│  │                        │  │                     │  │                 │  │
│  │ Tools: 7 specialized   │  │ Tools: Gmail,       │  │ Tools: Read-only│  │
│  │  - download_resume     │  │   Calendar, Chat,   │  │   Airtable,     │  │
│  │  - parse_resume_text   │  │   Airtable, PubSub  │  │   Gmail,        │  │
│  │  - analyze_fit         │  │                     │  │   Calendar,     │  │
│  │  - create_airtable_rec │  │ Methods:            │  │   Drive         │  │
│  │  - generate_icc_pdf    │  │  - generate_outreach│  │                 │  │
│  │  - upload_icc          │  │  - parse_reply      │  │ Model: Gemini   │  │
│  │  - publish_event       │  │  - approve_schedule │  │   1.5 Pro       │  │
│  │                        │  │                     │  │ Temp: 0.7       │  │
│  │ Model: Gemini 1.5 Pro  │  │ Workflows:          │  │                 │  │
│  │ Temp: 0.2              │  │  - Outreach         │  │ Purpose:        │  │
│  │ Max Tokens: 8192       │  │  - Scheduling       │  │  Conversational │  │
│  │                        │  │  - Reply parsing    │  │  data queries   │  │
│  │ Trigger: Drive PDF     │  │                     │  │                 │  │
│  │   upload in Resumes/   │  │ Triggers:           │  │ Trigger:        │  │
│  │                        │  │  - Airtable updates │  │  Chat commands  │  │
│  │ Output: Applicant +    │  │  - Gmail replies    │  │  Manual API     │  │
│  │   Pipeline records,    │  │  - Chat approvals   │  │                 │  │
│  │   ICC PDF              │  │                     │  │                 │  │
│  └────────────────────────┘  └─────────────────────┘  └─────────────────┘  │
│                                                                               │
└────────┬──────────────────────┬─────────────────────┬────────────────────────┘
         │                      │                     │
         v                      v                     v
┌─────────────────────────────────────────────────────────────────────────────┐
│                            TOOLS LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Airtable    │  │    Gmail     │  │   Calendar   │  │    Drive     │   │
│  │  (10 tools)  │  │  (6 tools)   │  │  (4 tools)   │  │  (4 tools)   │   │
│  │              │  │              │  │              │  │              │   │
│  │ • create_app │  │ • create_draf│  │ • create_even│  │ • download   │   │
│  │ • get_app    │  │ • send_draft │  │ • get_event  │  │ • upload     │   │
│  │ • update_app │  │ • send_msg   │  │ • list_events│  │ • get_meta   │   │
│  │ • find_apps  │  │ • get_msg    │  │ • find_free  │  │ • list_folder│   │
│  │ • create_pip │  │ • get_thread │  │              │  │              │   │
│  │ • get_pip    │  │ • list_threa │  │              │  │              │   │
│  │ • update_pip │  │              │  │              │  │              │   │
│  │ • find_by_th │  │              │  │              │  │              │   │
│  │ • log_intera │  │              │  │              │  │              │   │
│  │ • create_con │  │              │  │              │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────────┐  │
│  │    Chat      │  │   Pub/Sub    │  │   Applicant Analysis Tools       │  │
│  │  (4 tools)   │  │  (5 tools)   │  │        (7 ADK tools)             │  │
│  │              │  │              │  │                                  │  │
│  │ • post_msg   │  │ • publish    │  │ • download_resume (base64)       │  │
│  │ • post_appro │  │ • pub_airta  │  │ • parse_resume (PDF→dict)        │  │
│  │ • post_notif │  │ • pub_gmail  │  │ • analyze_fit (LLM)              │  │
│  │ • post_app_s │  │ • pub_drive  │  │ • create_records (Airtable)      │  │
│  │              │  │ • pub_chat   │  │ • generate_icc (reportlab)       │  │
│  │              │  │              │  │ • upload_icc (Drive)             │  │
│  │              │  │              │  │ • publish_event (Pub/Sub)        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────────────┘  │
│                                                                               │
└────────┬──────────────────────┬──────────────────────┬───────────────────────┘
         │                      │                      │
         v                      v                      v
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL APIS & SERVICES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                │
│  │ Google         │  │   Airtable     │  │  Vertex AI     │                │
│  │ Workspace API  │  │      API       │  │    (Gemini)    │                │
│  │                │  │                │  │                │                │
│  │ • Gmail        │  │ • Applicants   │  │ • Gemini 1.5   │                │
│  │ • Calendar     │  │ • Pipeline     │  │    Pro         │                │
│  │ • Drive        │  │ • Interactions │  │ • Reasoning    │                │
│  │ • Chat         │  │ • Contractors  │  │    Engines     │                │
│  │ • Meet         │  │                │  │                │                │
│  └────────────────┘  └────────────────┘  └────────────────┘                │
│                                                                               │
│  ┌────────────────┐  ┌────────────────┐                                     │
│  │  GCP Pub/Sub   │  │  Cloud Run     │                                     │
│  │                │  │                │                                     │
│  │ • Topics       │  │ • Webhooks svc │                                     │
│  │ • Subscriptions│  │ • PubSub svc   │                                     │
│  └────────────────┘  └────────────────┘                                     │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Example: Resume Upload → Applicant Profile

```
1. HR uploads resume.pdf to Drive "Resumes" folder
   │
2. Drive Push Notification → POST /webhooks/drive
   │
3. Webhook receiver publishes to jetsmx-drive-events
   │
4. Pub/Sub delivers to /pubsub/drive endpoint
   │
5. route_drive_event() → drive_handler.handle_resume_upload()
   │
6. Invokes: applicant_analysis_agent.process_resume(file_id, filename)
   │
7. Agent executes 7-step workflow using Gemini reasoning:
   ├─ download_resume_from_drive(file_id)
   ├─ parse_resume_text(pdf_base64)
   ├─ analyze_candidate_fit(parsed_data_json) [LLM call]
   ├─ create_applicant_records_in_airtable(...)
   ├─ generate_icc_pdf(...)
   ├─ upload_icc_to_drive(...)
   └─ publish_completion_event(...)
   │
8. Result: Applicant + Pipeline records in Airtable, ICC PDF in Drive
   │
9. Event published to jetsmx-applicant-events topic
   │
10. (Future) Trigger downstream workflows (e.g., auto-approve if strong fit)
```

---

## 7. Gaps & Recommendations

### 7.1 Missing Pieces

#### Incomplete Workflows
1. **Meeting Analysis Agent** - Planned but not implemented
   - Purpose: Analyze probe call and interview transcripts
   - Tools needed: Speech-to-text, transcript parsing, update Airtable
   - File: `agents/meeting_analysis/` exists but empty

2. **Contractor Management** - Partially implemented
   - `airtable_create_contractor` tool exists
   - No agent or workflow to trigger contractor creation
   - Missing: Job dispatch, availability tracking, performance reviews

3. **Background Check Integration** - Planned in routing rules
   - Event rule exists: `Background Check Status = "Passed"` → create_contractor_record
   - No actual background check API integration
   - Missing: Checkr/Sterling integration, status polling

4. **Offer Management** - Not implemented
   - Missing: Offer letter generation, signature tracking, onboarding checklist

#### Unused Tools
1. **Drive Permissions** - Module exists but no LangGraph tool wrapper
   - File: `tools/drive/permissions.py`
   - Functions: `share_file()`, `get_permissions()`, `remove_permission()`
   - Use case: Share ICC PDFs with applicants

2. **Gmail Watch Setup** - Utility exists but not agent-accessible
   - File: `tools/gmail/watch.py`
   - Function: `setup_watch()`, `stop_watch()`
   - Use case: Dynamically manage Gmail push notifications

#### Missing Error Handling
1. **No Retry Logic** - Tools fail immediately on errors
   - Recommendation: Implement exponential backoff for transient failures
   - Libraries: `tenacity`, `backoff`

2. **No Circuit Breaker** - Repeated failures to external APIs not handled
   - Recommendation: Circuit breaker pattern to prevent cascading failures
   - Library: `pycircuitbreaker`

3. **No Fallback Strategies** - If Gemini LLM unavailable, workflow fails
   - Recommendation: Fallback to simpler heuristic analysis
   - Example: Rule-based candidate scoring if LLM times out

4. **Limited Validation** - Input data not validated before processing
   - Recommendation: Pydantic validation on all tool inputs
   - Example: Validate email format, phone format, date format

5. **No Dead Letter Queue** - Failed Pub/Sub messages are retried then discarded
   - Recommendation: DLQ for manual review of failed events
   - GCP: Configure dead letter topic on subscriptions

#### Future Enhancements (from Implementation Summary)
1. **Batch Processing** - One resume at a time currently
   - Recommendation: Batch API endpoint to process multiple resumes

2. **Streaming Responses** - User waits for complete workflow
   - Recommendation: SSE or WebSocket for real-time progress updates

3. **A/B Testing Framework** - No way to test prompt variations
   - Recommendation: Prompt versioning, parallel execution, metrics

4. **Multi-modal Analysis** - PDFs only
   - Recommendation: Extract images, analyze certifications, video resumes

5. **Predictive Analytics** - No machine learning on historical data
   - Recommendation: Train models to predict candidate success

### 7.2 Inconsistencies

#### Duplicated Functionality
1. **Two Applicant Analysis Implementations**
   - `agent_adk.py` (current) and `graph.py` (legacy)
   - Recommendation: Deprecate LangGraph version after ADK validation
   - Timeline: Keep both for 30-day parallel run, then remove graph.py

2. **Two Airtable Clients**
   - `tools/airtable/client.py` (main client)
   - `tools/airtable_tools.py` (older wrapper?)
   - Recommendation: Audit and consolidate

3. **Two Gmail Tool Files**
   - `tools/gmail/tools.py` (LangGraph wrappers)
   - `tools/gmail_tools.py` (duplicate?)
   - Recommendation: Remove `gmail_tools.py` if redundant

#### Naming Inconsistencies
1. **Table/Field Names** - Hardcoded strings vs constants
   - Example: `"applicant_pipeline"` string in router.py
   - Recommendation: Use `constants.APPLICANT_PIPELINE_TABLE` everywhere

2. **Event Types** - Inconsistent naming
   - Some events: `"applicant_profile_created"`
   - Others: `"airtable_applicant_pipeline_updated"`
   - Recommendation: Standardize: `<source>.<resource>.<action>` format

#### Outdated Files
1. **examples/agent_with_guardrails.py** - Example file
   - Not integrated with current architecture
   - Recommendation: Update or remove

2. **scripts/test_workflows.py** - Test script
   - May not reflect current ADK implementation
   - Recommendation: Update to test ADK agent

### 7.3 Architecture Improvements

#### 1. Centralized Configuration
**Current:** Settings scattered across multiple files
**Recommendation:** Single source of truth for all config
```python
# config/agents.yaml
agents:
  applicant_analysis:
    model: "gemini-1.5-pro"
    temperature: 0.2
    max_tokens: 8192
    tools:
      - download_resume_from_drive
      - parse_resume_text
      # ...
```

#### 2. Observability Enhancements
**Current:** Basic logging, no metrics
**Recommendation:**
- OpenTelemetry tracing across agents
- Prometheus metrics for tool invocations
- Grafana dashboards for workflow visualization
- Alerting on error rates, latency spikes

#### 3. Testing Strategy
**Current:** Unit tests for some tools
**Recommendation:**
- Integration tests for full workflows
- End-to-end tests with test Airtable base
- Mocked external APIs for CI/CD
- Property-based testing for parsers

#### 4. Deployment Pipeline
**Current:** Manual deployment scripts
**Recommendation:**
- GitHub Actions or Cloud Build CI/CD
- Terraform for infrastructure-as-code
- Automated testing before deploy
- Blue-green deployments for zero-downtime

#### 5. Security Enhancements
**Current:** Basic webhook auth
**Recommendation:**
- Rotate service account keys regularly
- Implement least-privilege IAM roles
- PII detection and redaction
- Secrets management (GCP Secret Manager)
- Rate limiting on webhooks

#### 6. Cost Optimization
**Current:** No cost tracking
**Recommendation:**
- Monitor Gemini API usage
- Cache LLM responses for duplicate resumes
- Optimize Pub/Sub message sizes
- Cloud Run autoscaling tuning

#### 7. Disaster Recovery
**Current:** No backup/restore strategy
**Recommendation:**
- Airtable export backups
- Drive file versioning
- Event replay capability from Pub/Sub
- Runbook for common failures

### 7.4 Specific Recommendations by Priority

#### High Priority (Do First)
1. ✅ **Deploy ADK Agent to Production** - Already implemented, needs deployment
2. ✅ **Add Retry Logic to All Tools** - Prevent transient failures
3. ✅ **Implement Dead Letter Queue** - Capture failed events for review
4. ✅ **Add Input Validation** - Pydantic models on all tool parameters
5. ✅ **Deprecate LangGraph Version** - After ADK validation period

#### Medium Priority (Next 3 Months)
1. **Implement Meeting Analysis Agent** - Transcript processing
2. **Add Background Check Integration** - Checkr or Sterling API
3. **Build Contractor Management Workflows** - Job dispatch, tracking
4. **Create Analytics Dashboard** - Hiring funnel metrics
5. **Add Observability** - OpenTelemetry + Prometheus

#### Low Priority (Future)
1. **QuickBooks Integration** - Invoicing, payments
2. **DocuSign Integration** - Contract signatures
3. **Multi-modal Resume Analysis** - Images, videos
4. **Predictive Analytics** - ML models for candidate success
5. **Mobile App** - On-the-go applicant review

### 7.5 Technical Debt

#### Code Quality
- Missing type hints in some files
- Inconsistent error handling patterns
- Some functions too long (>100 lines)
- Limited docstrings on internal functions

#### Documentation
- API documentation not auto-generated
- Workflow diagrams not maintained
- Onboarding guide missing
- Troubleshooting guide incomplete

#### Infrastructure
- Terraform modules incomplete
- No staging environment
- Manual secret management
- Cloud Run services not auto-scaled optimally

---

## Summary

### What's Working Well ✅
1. **Comprehensive Tool Library** - 46 well-structured tools covering all major APIs
2. **Event-Driven Architecture** - Scalable, decoupled, async processing
3. **Human-in-the-Loop** - Approval workflows prevent errors
4. **ADK Implementation** - Modern, flexible agent framework
5. **Audit Trail** - Complete logging of all actions
6. **Modular Design** - Easy to add new agents/tools

### What Needs Attention ⚠️
1. **Error Handling** - Add retries, circuit breakers, validation
2. **Observability** - Metrics, tracing, alerting
3. **Testing** - More integration and E2E tests
4. **Documentation** - Keep diagrams and guides updated
5. **Deployment** - Automate with CI/CD
6. **Cost Tracking** - Monitor LLM and API usage

### What's Missing ❌
1. **Meeting Analysis Agent**
2. **Contractor Management**
3. **Background Check Integration**
4. **QuickBooks & DocuSign**
5. **Analytics Dashboard**

---

**End of System Overview**  
**Next Steps:** Deploy ADK agent, add error handling, implement meeting analysis

