# ArcVault AI Automated Workflow

AI-powered intake, classification, enrichment, routing, and escalation workflow for ArcVault customer requests.

This project was built for the Valsoft AI Engineer Technical Assessment. It simulates an automated triage pipeline for a B2B software company receiving unstructured customer requests through email, web forms, support portals, or API/webhook-style inputs.

The workflow processes each request, classifies it with an LLM, extracts key information, routes it to the correct queue, checks whether human escalation is required, and saves a structured JSON output record.

---

## 1. What This Project Does

For every inbound customer request, the workflow produces:

- Category
- Priority
- Confidence score
- Core issue
- Extracted identifiers
- Urgency signal
- Routing destination
- Human escalation flag
- Escalation reasons
- Human-readable summary
- Final structured JSON record

The five required assessment sample inputs are included in:

```text
app/sample_data.py
```

The generated output records are saved in:

```text
outputs/processed_requests.json
```

---

## 2. Architecture

```text
Streamlit Dashboard
        ↓
FastAPI Backend
        ↓
LangGraph Workflow
        ↓
Groq LLM
        ↓
Pydantic Structured Output
        ↓
Routing + Escalation Rules
        ↓
JSON Output File
```

### Main tools used


| Tool      | Purpose                                         |
| --------- | ----------------------------------------------- |
| FastAPI   | Exposes the workflow through API endpoints      |
| LangGraph | Orchestrates the multi-step workflow            |
| Groq      | Runs the LLM classification and enrichment step |
| Pydantic  | Validates structured inputs and LLM outputs     |
| Streamlit | Provides a simple demo dashboard                |
| JSON file | Stores the final structured output records      |


---

## 3. Why This Architecture

I separated the workflow into clear responsibilities:

- The **LLM** understands the unstructured customer message.
- **Pydantic** validates that the LLM output follows the expected schema.
- **LangGraph** manages the workflow steps and shared state.
- **Python rules** handle routing and escalation decisions.
- **FastAPI** exposes the workflow as a backend service.
- **Streamlit** makes the workflow easy to demonstrate visually.

This keeps the system explainable, testable, and easier to extend.

---

## 4. Workflow Steps

The LangGraph workflow follows this sequence:

```text
initialize_request
→ analyze_with_llm
→ route_request
→ evaluate_escalation
→ finalize_and_save_record
```

### Step 1 — Ingestion

A request enters the system through FastAPI, Streamlit, or the included sample data.

### Step 2 — Classification

The LLM classifies the request into one of:

- Bug Report
- Feature Request
- Billing Issue
- Technical Question
- Incident/Outage

It also assigns:

- Priority: Low, Medium, or High
- Confidence score between 0.0 and 1.0

### Step 3 — Enrichment

The LLM extracts:

- Core issue
- Account IDs
- Invoice numbers
- Error codes
- Product or integration names
- Monetary amounts
- Time references
- Affected scope
- Urgency signal
- Summary for the receiving team

### Step 4 — Routing

Routing is deterministic and handled in Python.


| Category           | Default Queue     |
| ------------------ | ----------------- |
| Bug Report         | Engineering Queue |
| Feature Request    | Product Queue     |
| Billing Issue      | Billing Queue     |
| Technical Question | IT/Security Queue |
| Incident/Outage    | Engineering Queue |


### Step 5 — Escalation

If escalation is required, the final destination becomes:

```text
Human Escalation Queue
```

Escalation happens when:

- Confidence is below `0.70`
- The request is classified as `Incident/Outage`
- The message contains service-impact language
- Multiple users or a wider team are affected
- A billing discrepancy appears greater than `$500`

Low-confidence cases are treated as fallback cases and routed to the Human Escalation Queue.

### Step 6 — Structured Output

Each processed record is saved to:

```text
outputs/processed_requests.json
```

---

## 5. Billing Escalation Note

For billing issues, I interpreted “billing error > $500” as the **difference between the charged amount and the expected amount**, not the full invoice value.

Example:

```text
Invoice charge: $1,240
Contract rate: $980
Difference: $260
```

Because the discrepancy is `$260`, the request is routed to Billing but is not escalated by amount.

This avoids over-escalating normal invoices simply because the invoice total is greater than `$500`.

---

## 6. Project Structure

```text
elissa-arcvault-automated-workflow/
│
├── app/
│   ├── __init__.py
│   ├── schemas.py
│   ├── state.py
│   ├── sample_data.py
│   ├── prompts.py
│   ├── llm_client.py
│   ├── routing.py
│   ├── escalation.py
│   ├── persistence.py
│   ├── graph.py
│   └── main.py
│
├── dashboard/
│   └── streamlit_app.py
│
├── outputs/
│   └── processed_requests.json
│
├── prompts/
│   └── triage_prompt.md
│
├── docs/ 
│   └── Architecture_writeup.md
│   └── prompts_documentation.md
│   
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 7. Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/elissadiab/elissa-valsoft-assessment.git
cd elissa-arcvault-automated-workflow
```

Replace `YOUR_USERNAME` with the correct GitHub username.

---

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Create a `.env` file

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
```

Do not commit `.env` to GitHub.

---

## 8. Running the Project

The project has two parts:

1. FastAPI backend
2. Streamlit dashboard

Run them in two separate terminals.

---

### Terminal 1 — Start FastAPI

```bash
uvicorn app.main:app --reload --port 8000
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "ArcVault AI Intake & Triage API"
}
```

---

### Terminal 2 — Start Streamlit

Activate the environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run Streamlit:

```bash
streamlit run dashboard/streamlit_app.py
```

Open:

```text
http://localhost:8501
```

The Streamlit dashboard expects FastAPI to be running at:

```text
http://127.0.0.1:8000
```

---

## 9. How to Use the Demo

1. Start FastAPI.
2. Start Streamlit.
3. Open the Streamlit dashboard.
4. Click **Check API Health** in the sidebar.
5. Go to **Batch Run Samples**.
6. Click **Run All 5 Samples**.
7. Review the table and detailed records.
8. Go to **Results Dashboard**.
9. View or download the generated JSON output.

---

## 10. FastAPI Endpoints


| Method | Endpoint          | Description                      |
| ------ | ----------------- | -------------------------------- |
| GET    | `/`               | Basic welcome route              |
| GET    | `/health`         | API health check                 |
| POST   | `/triage`         | Process one custom request       |
| POST   | `/triage/samples` | Process the five sample requests |
| GET    | `/results`        | Read saved output records        |
| DELETE | `/results`        | Clear saved output records       |


Example request for `/triage`:

```json
{
  "source": "Email",
  "raw_message": "Hi, I tried logging in and keep getting a 403 error."
}
```

---

## 11. Command-Line Testing

### Test one sample request

```bash
python -c "from app.graph import process_request; from app.sample_data import SAMPLE_REQUESTS; record = process_request(SAMPLE_REQUESTS[0]); print(record.model_dump_json(indent=2))"
```

### Test all five sample requests

```bash
python -c "from app.graph import process_request; from app.sample_data import SAMPLE_REQUESTS; from app.persistence import clear_processed_records; clear_processed_records(); records = [process_request(req) for req in SAMPLE_REQUESTS]; print(f'processed {len(records)} records'); [print(r.request_id, r.category.value, r.priority.value, r.destination_queue.value, r.human_escalation_required) for r in records]"
```

Expected output shape:

```text
processed 5 records
REQ-001 Bug Report Medium Engineering Queue False
REQ-002 Feature Request Medium Product Queue False
REQ-003 Billing Issue Medium Billing Queue False
REQ-004 Technical Question Medium IT/Security Queue False
REQ-005 Incident/Outage High Human Escalation Queue True
```

---

## 12. Sample Output

Example processed record:

```json
{
  "request_id": "REQ-001",
  "source": "Email",
  "raw_message": "Hi, I tried logging in this morning and keep getting a 403 error...",
  "category": "Bug Report",
  "priority": "Medium",
  "confidence_score": 0.9,
  "core_issue": "The customer is experiencing a 403 error when trying to log in after the latest update.",
  "extracted_entities": {
    "account_ids": ["arcvault.io/user/jsmith"],
    "invoice_numbers": [],
    "error_codes": ["403"],
    "product_or_integration_names": [],
    "monetary_amounts": [],
    "time_references": ["last Tuesday"],
    "affected_scope": "single user"
  },
  "urgency_signal": "Medium",
  "destination_queue": "Engineering Queue",
  "human_escalation_required": false,
  "escalation_reasons": [],
  "model_provider": "groq",
  "model_name": "llama-3.3-70b-versatile",
  "workflow_version": "1.0"
}
```

---

## 13. Production Improvements

If this workflow were moved to production, I would add:

- Retry logic for failed LLM calls
- Request timeouts and fallback handling
- API authentication
- Secret management through a vault
- Structured logging and tracing
- Per-node latency monitoring
- Database persistence instead of JSON files
- Human review dashboard
- Evaluation dataset for classification accuracy
- Prompt versioning
- Integration with ticketing systems such as Jira, Zendesk, or HubSpot

---

## 14. Phase 2 Ideas

With another week, I would focus on making the workflow more useful after the initial triage step.

1. **Support team review dashboard**  

   I would improve the dashboard so support team members can review routed requests, mark what action they took, update the status, flag wrong classifications, and record how the issue was resolved. This would create a feedback loop to improve the prompt, routing rules, and escalation logic over time.

2. **Automated customer replies**  

   I would add automated customer reply drafts. After a request is classified and routed, the system could prepare a short acknowledgement message telling the customer that the request was received, which team will handle it, and what the next step is.

3. **Documentation-based LLM assistant**  

   For Technical Questions, I would add a documentation-based LLM assistant. The system could search ArcVault’s product documentation and suggest an answer when confidence is high. If the answer is unclear or unsupported by the documentation, the request would stay routed to IT/Security for human review.

4. **Production readiness improvements**  

   I would also add production improvements such as Google Sheets or ticketing-system integration, model fallback if Groq is unavailable, and Docker support for easier setup and reproducibility.



---

## 15. Summary

This project demonstrates a complete AI automation workflow for customer request triage.

The core design principle is separation of responsibility:

```text
LLM → understands and structures the message
Pydantic → validates the output
LangGraph → orchestrates the workflow
Python rules → route and escalate
FastAPI → exposes the workflow as an API
Streamlit → demonstrates the workflow visually
JSON → stores the final output
```

This makes the system clear, testable, auditable, and ready for future production improvements.



