# **Architecture Write-Up**

## **1. System Design**

I started the project by breaking the assessment into the required workflow steps: ingestion, classification, enrichment, routing, escalation, and structured output. Before writing the full logic, I defined the main objects moving through the system using Pydantic schemas: CustomerRequest, LLMTriageAnalysis, ExtractedEntities, RoutingResult, EscalationResult, and ProcessedTriageRecord. This helped me keep each step clear because every function had a defined input and output instead of passing unstructured dictionaries around.

The backend is built with **FastAPI**. I used FastAPI because the workflow is API-first: a request can come from a webhook, form, support portal, or any other system. FastAPI exposes endpoints to process one request, run the five sample requests, read saved results, clear results, and check health. I have used Flask before, but **FastAPI** was a better fit here because it works naturally with **Pydantic** and automatically supports structured request/response validation.

The workflow is orchestrated with LangGraph. I am familiar with LangChain,LLamaIndex and Langraph but I chose LangGraph because this is not only one prompt call. It is a multi-step process where each step adds information to the shared workflow state. In [graph.py](http://graph.py), the request moves through these nodes: initialize request metadata, analyze with the LLM, route the request, evaluate escalation, and finalize/save the record. The state is held inside TriageWorkflowState while the request is being processed.

The LLM client uses **Groq**. I had previously worked more with Gemini and other LLM APIs, so I used this assessment as an opportunity to try Groq because it is fast and suitable for classification/extraction tasks. The model temperature is set to 0 because the workflow needs consistent outputs, not creative answers.

I also added a **Streamlit** dashboard because I usually use Streamlit in AI projects to quickly build a clear interface for testing and presenting results. In this project, Streamlit is only a demo layer. The real workflow remains in FastAPI and LangGraph. Streamlit calls the API, displays the triage result, and allows running the five assessment samples visually.

The architecture is:

Streamlit Dashboard → FastAPI API → LangGraph Workflow → Groq LLM → Routing/Escalation Rules → JSON Output

The final records are saved in outputs/processed_requests.json through the persistence layer. I chose JSON because the assessment asks for a structured output file, and it is easy to review and submit.

## **2. Routing Logic**

The LLM is responsible for understanding the raw customer message and assigning a category. However, I did not let the LLM directly choose the final destination queue. Routing is handled in code using deterministic rules because it should be predictable, easy to audit, and easy to modify.

The mapping is:

- Bug Report → Engineering Queue
- Feature Request → Product Queue
- Billing Issue → Billing Queue
- Technical Question → IT/Security Queue
- Incident/Outage → Engineering Queue initially, unless escalation overrides it

I mapped Bug Reports and Incidents to Engineering because they usually require technical investigation. Feature Requests go to Product because they affect roadmap and prioritization. Billing Issues go to Billing because they involve invoices, charges, or contract rates. Technical Questions go to IT/Security because the examples involve setup, SSO, authentication, integrations, and access-related questions.

This separation keeps the LLM focused on language understanding, while the business rules remain controlled in Python. If the company later wants to change a queue mapping, I can update the routing file without changing the LLM prompt.

## **3. Escalation Logic**

Escalation is evaluated after classification and routing. I kept this **logic rule-based** because escalation decisions **should be easy to explain and test.**

A request is flagged for human review if the confidence score is below 0.70 or if it matches risk criteria such as outage/service-impact language, multiple users affected, security or compliance risk, data loss risk, or a large billing discrepancy. When escalation is required, the final destination is changed to the Human Escalation Queue.

For example, the dashboard loading sample is classified as Incident/Outage, has High priority, mentions multiple affected users, and is routed to the Human Escalation Queue. This shows that the system does not treat urgent service-impacting cases like normal tickets.

**The tradeoff is that this approach may create some false positives**, but I prefer that for this type of workflow. It is safer to escalate an ambiguous or r**isky case than to route it incorrectly without review.**

## **4. Structured Output**

The final output is built as a ProcessedTriageRecord and saved to outputs/processed_requests.json. Each record includes the original message, category, priority, confidence score, extracted entities, urgency signal, summary, destination queue, routing reason, escalation flag, escalation reasons, model metadata, and processing duration.

I separated persistence into its own file so the storage layer can be replaced later. For the assessment, a JSON file is enough. In production, the same persistence layer could be replaced with a database, Google Sheet, ticketing system, or webhook integration.

## **5. Production Improvements**

In production, I would replace the local JSON file with a database or a ticketing-system integration so the workflow can handle concurrent requests safely. I would also add retries, timeout handling, fallback models, structured logging, and monitoring around the LLM call.

For latency and cost, I would track processing time, token usage, confidence scores, and category distribution. Clear cases could potentially be handled with a smaller model or simple rules, while ambiguous cases could go to a stronger model. I would also add authentication to the API and dashboard, and avoid logging sensitive customer data unnecessarily.

## **6. Phase 2**

If I had another week, I would add a human feedback loop. If a reviewer **corrects a category**, priority, route, or escalation decision, that correction could be saved and **used to improve the prompt and test cases.**

If I had another week, I would improve the workflow for the support team after triage. The interface could allow team members to review routed requests, mark what action they took, flag wrong classifications, and record how the issue was resolved. This would create a useful feedback loop for improving the system.

I would also add automated customer replies. After triage, the system could draft a short acknowledgement message explaining that the request was received, which team will handle it, and what the next step is.

For Technical Questions, I would add a documentation-based LLM assistant. The system could search ArcVault’s docs and suggest an answer when confidence is high. If the answer is unclear, the request would stay routed to IT/Security for human review.

And overall, I would keep the architecture simple on purpose: FastAPI handles intake, LangGraph handles orchestration, Groq handles language understanding, Python rules handle routing and escalation, and the persistence layer saves the structured output.

  
