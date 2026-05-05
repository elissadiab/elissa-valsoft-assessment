"""
schemas.py

Defines the data structures used in our AI triage workflow.

Python classes that desribe what each object should look like.
For example:
- What does an incoming customer request contain?
- What should the LLM return?
- What should a routing decision contain?
- What should an escalation decision contain?
- What should the final saved JSON record look like?

We use Pydantic because it validates the data automatically.
This is useful in AI workflows because LLMs can sometimes return messy or unexpected outputs.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# List of supported channels where a request can enter the workflow.
class RequestSource(str, Enum):
    EMAIL = "Email"
    WEB_FORM = "Web Form"
    SUPPORT_PORTAL = "Support Portal"
    WEBHOOK = "Webhook"
    MANUAL_ENTRY = "Manual Entry"


# List of categories required by the assessment.
class RequestCategory(str, Enum):
    BUG_REPORT = "Bug Report"
    FEATURE_REQUEST = "Feature Request"
    BILLING_ISSUE = "Billing Issue"
    TECHNICAL_QUESTION = "Technical Question"
    INCIDENT_OUTAGE = "Incident/Outage"


# Priority assigned to the request based on impact and urgency. (Classification step)
class PriorityLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


# Urgency signal extracted from the message content. (Enrichement step: extract core information)
class UrgencyLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


# Internal destination queues used by the routing logic + Human Escalation.
class DestinationQueue(str, Enum):
    ENGINEERING = "Engineering Queue"
    PRODUCT = "Product Queue"
    BILLING = "Billing Queue"
    IT_SECURITY = "IT/Security Queue"
    HUMAN_ESCALATION = "Human Escalation Queue"


# Raw customer request before AI processing.
class CustomerRequest(BaseModel):
    request_id: Optional[str] = Field(
        default=None,
        description="Optional request identifier. If missing, the workflow can generate one.",
    )
    source: RequestSource = Field(
        description="Channel where the customer request was received.",
    )
    raw_message: str = Field(
        min_length=1,
        description="Unstructured customer message.",
    )


# Structured entities extracted from the raw message by the LLM.
class RequestEntities(BaseModel):
    account_ids: Optional[List[str]] = Field(
        default_factory=list,
        description="Account IDs, usernames, or account URLs mentioned in the message. Use [] if none.",
    )
    invoice_numbers: Optional[List[str]] = Field(
        default_factory=list,
        description="Invoice or order numbers mentioned in the message. Use [] if none.",
    )
    error_codes: Optional[List[str]] = Field(
        default_factory=list,
        description="Error codes mentioned in the message, such as 403 or 500. Use [] if none.",
    )
    product_or_integration_names: Optional[List[str]] = Field(
        default_factory=list,
        description="Product areas or third-party integrations mentioned, such as Okta or SSO. Use [] if none.",
    )
    monetary_amounts: Optional[List[str]] = Field(
        default_factory=list,
        description="Monetary amounts mentioned in the message. Use [] if none.",
    )
    time_references: Optional[List[str]] = Field(
        default_factory=list,
        description="Time references mentioned in the message, such as 'last Tuesday' or '2pm EST'. Use [] if none.",
    )
    affected_scope: Optional[str] = Field(
        default=None,
        description="Affected user scope, such as single user, multiple users, all users, or unknown.",
    )

    @field_validator(
        "account_ids",
        "invoice_numbers",
        "error_codes",
        "product_or_integration_names",
        "monetary_amounts",
        "time_references",
        mode="before",
    )
    @classmethod
    def convert_null_lists_to_empty_lists(cls, value):
        if value is None:
            return []
        return value
    

# Structured result returned by the LLM after classification and enrichment.
class AIAnalysisResult(BaseModel):
    category: RequestCategory = Field(
        description="Best matching request category.",
    )
    priority: PriorityLevel = Field(
        description="Priority level based on business impact and urgency.",
    )
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Model confidence between 0.0 and 1.0.",
    )
    core_issue: str = Field(
        min_length=1,
        description="One neutral sentence describing the customer's main issue.",
    )
    extracted_entities: RequestEntities = Field(
        description="Structured identifiers and entities extracted from the request.",
    )
    urgency_signal: UrgencyLevel = Field(
        description="Low, Medium, or High urgency signal.",
    )
    summary: str = Field(
        min_length=1,
        description="Two to three sentence summary for the receiving team: the problem, who is affected, and recommended next action.",
    )
    
    


# Deterministic routing result produced after the LLM classification.
class RoutingResult(BaseModel):
    destination_queue: DestinationQueue = Field(
        description="Queue where the request should be routed.",
    )
    routing_reason: str = Field(
        description="Short explanation of why this queue was selected.",
    )


# Human review decision produced by escalation rules.
class EscalationResult(BaseModel):
    human_escalation_required: bool = Field(
        description="True if the request should be routed to human review.",
    )
    escalation_reasons: List[str] = Field(
        default_factory=list,
        description="One or more reasons that triggered escalation.",
    )


# Final record saved to the output JSON file.
class ProcessedTriageRecord(BaseModel):
    request_id: str
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the message entered the workflow.",
    )
    processed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the workflow finished processing.",
    )

    source: RequestSource
    raw_message: str

    category: RequestCategory
    priority: PriorityLevel
    confidence_score: float

    core_issue: str
    extracted_entities: RequestEntities
    urgency_signal: UrgencyLevel
    summary: str

    destination_queue: DestinationQueue
    routing_reason: str

    human_escalation_required: bool
    escalation_reasons: List[str]

    model_provider: str
    model_name: str
    workflow_version: str = "1.0"
    processing_duration_ms: int


# FastAPI response model for processing one request.
class SingleTriageResponse(BaseModel):
    success: bool = True
    record: ProcessedTriageRecord


# FastAPI response model for processing multiple requests.
class BatchTriageResponse(BaseModel):
    success: bool = True
    total_processed: int
    records: List[ProcessedTriageRecord]