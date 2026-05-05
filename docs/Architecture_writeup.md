# Architecture Write-Up

## 1. Overall System Design

For this project, I treated the assessment as a real intake and triage workflow, not only as one LLM prompt. I first broke the problem into the required steps: accepting a raw customer request, classifying it, extracting useful information, routing it to the right team, checking if it needs human escalation, and saving a structured output record.

Before coding the workflow itself, I started by defining the data objects that would move between the steps. I created schemas for the incoming request, the LLM analysis, the extracted entities, the routing result, the escalation result, and the final processed record. This helped me keep the project organized because each step had a clear input and output. Instead of passing random dictionaries around, I wanted the workflow to be structured and easy to validate.

The backend is built with FastAPI. FastAPI acts as the intake layer and exposes endpoints to process a single request, run the five assessment samples, read saved records, clear saved records, and check the service health. I have used Flask before, but I chose FastAPI here because this project is more API-first and schema-driven. FastAPI also works very well with Pydantic, so it made sense to use both together for clean request and response validation.

The workflow itself is built with LangGraph. I am already familiar with LangChain and have used it in AI projects before, but I chose LangGraph because this problem is a multi-step workflow, not just a simple chain. Each step depends on the previous step and adds information to a shared state. LangGraph made it easier to represent the process as nodes: initialize request, analyze with the LLM, route the request, evaluate escalation, and save the final record. This also makes the workflow easier to explain and extend later.

For the LLM provider, I used Groq. I had worked more with Gemini and other LLM APIs before, so I saw this as a good opportunity to try Groq for a fast, low-cost hosted model. Since the task is classification and extraction, speed matters, and Groq was a good fit for that. I also set the temperature to `0` because I wanted consistent and repeatable outputs, not creative responses.

I also added a Streamlit dashboard as a demo interface. In many of my AI projects, I use Streamlit because it helps me quickly create a clean interface to test and present the workflow. Here, FastAPI remains the real backend, and Streamlit only calls the API and displays the results. I added it so the workflow is easier to review visually: the user can run one request, run the five samples, inspect the JSON output, and see routing and escalation decisions clearly.

So the architecture is:

`Streamlit Dashboard → FastAPI API → LangGraph Workflow → Groq LLM → Routing/Escalation Rules → JSON Output`

The state is held inside the LangGraph workflow while a request is being processed. Each node adds something to the state, and the final state is converted into a processed record. The final output is saved to `outputs/processed_requests.json`, which is the structured output file required by the assessment.

## 2. Routing Logic

For routing, I decided not to let the LLM directly choose the final queue. The LLM classifies the request, but the actual routing is done with deterministic Python rules. I chose this because routing is a business decision, and it should be predictable, explainable, and easy to change.

The mapping is simple and based on how support teams usually work. Bug Reports go to the Engineering Queue because they may require investigation into product behavior or code-level issues. Feature Requests go to the Product Queue because they are related to roadmap decisions and prioritization. Billing Issues go to the Billing Queue because they involve invoices, charges, payment problems, or contract pricing. Technical Questions go to the IT/Security Queue because these requests often involve SSO, authentication, configuration, integrations, permissions, or setup. Incidents and outages are initially mapped to Engineering because they usually need urgent technical investigation.

I liked this separation because the LLM is used for what it is good at: understanding unstructured language. The code is used for what should stay controlled: operational routing rules. If the company later wants Technical Questions to go to Customer Support instead of IT/Security, I can change the routing map without changing the prompt or LLM configuration.

I also included a fallback path for low-confidence classifications. If the model is not confident enough, the workflow does not fully trust the automated routing and flags the request for human review. This is important because the cost of routing an ambiguous request incorrectly can be higher than asking a human to review it.

## 3. Escalation Logic

Escalation is handled after the classification and routing step. I kept escalation rule-based because escalation is a sensitive decision and should be easy to audit. I did not want the system to rely only on the LLM’s judgment for deciding whether a case needs urgent human attention.

The workflow flags a request for human escalation if the confidence score is below `0.70` or if the message contains higher-risk signals. These include an incident or outage, service-impact language, multiple users affected, security or compliance risk, possible data loss, or a billing discrepancy above the threshold. For example, the dashboard loading issue in the sample data is routed to the Human Escalation Queue because it is an active service issue and multiple users are affected.

When escalation is required, the escalation queue overrides the standard routing destination. For example, an outage may be initially mapped to Engineering, but the final destination becomes Human Escalation Queue so it receives immediate review. I chose this design because urgent or risky cases should not be treated like normal tickets.

The tradeoff is that this approach may create some false positives. However, for an intake workflow, I think this is acceptable because it is safer to escalate a risky or ambiguous case than to silently send it to the wrong queue.

## 4. Structured Output and Persistence

The final structured record is saved in a local JSON file: `outputs/processed_requests.json`. I chose JSON because the assessment specifically asks for a structured output file, and JSON is easy to review, submit, and reuse. Each record contains the original message, category, priority, confidence score, extracted entities, urgency signal, summary, destination queue, routing reason, escalation flag, escalation reasons, model metadata, and processing duration.

For this assessment, a local JSON file is enough because the goal is to demonstrate the workflow clearly. I still separated persistence into its own file so it can be replaced later without changing the rest of the workflow. In a real system, I would replace the JSON file with a database, Google Sheet, ticketing system, or webhook integration.

## 5. What I Would Do Differently in Production

In production, the first thing I would improve is persistence. A local JSON file is good for the assessment, but it is not enough for concurrent users or high-volume traffic. I would use a database or connect directly to a ticketing system so records are stored safely and can be searched, filtered, and audited.

I would also add stronger reliability around the LLM call. This would include retries, timeout handling, fallback models, structured logging, and monitoring. LLM APIs can fail or return unexpected outputs, so schema validation and error handling would be very important. For higher volume, I would also move request processing into an asynchronous queue so the API can accept requests quickly without waiting for the LLM response in the same request cycle.

For cost and latency, I would track model usage, response time, and confidence scores. Some requests may not need a large model; for example, clear billing issues or obvious feature requests could potentially be handled with a smaller model or rule-based pre-classification. More ambiguous cases could be sent to a stronger model. This would help balance accuracy, cost, and speed.

I would also add authentication and access control around the API and dashboard. Since support messages can contain sensitive customer data, I would avoid logging raw sensitive content unnecessarily and would consider redacting private identifiers from logs.

## 6. Phase 2

If I had another week, I would add a human feedback loop. When a reviewer corrects a category, priority, route, or escalation decision, that correction could be saved and used to improve the prompt and evaluation set. This would make the system improve over time instead of staying static.

I would also create a larger test set with ambiguous customer messages. The five sample inputs are useful, but they do not cover enough edge cases. I would especially test cases where the model might confuse Bug Report with Technical Question, or Bug Report with Incident/Outage.

Another Phase 2 improvement would be adding real downstream integrations. Instead of only saving to JSON, the system could create a ticket in Jira or Zendesk, send Slack alerts for escalations, or update a Google Sheet for reporting. I would also improve the Streamlit dashboard with filters, search, and simple analytics showing how many requests went to each category, queue, and escalation status.

Overall, I kept this version simple on purpose. I wanted the workflow to be easy to run, easy to review, and easy to explain. The main architecture decision was to separate the responsibilities clearly: FastAPI handles intake, LangGraph handles orchestration, the LLM handles language understanding, Python rules handle routing and escalation, and the persistence layer saves the final structured output.