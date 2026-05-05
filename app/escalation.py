"""
escalation.py

Contains human escalation logic for the ArcVault triage workflow.

Escalation is handled with deterministic rules instead of relying only on the LLM.
This makes the workflow easier to audit, explain, and adjust.

A request is escalated when:
- the LLM confidence is below 0.70
- the request is classified as an incident/outage
- the message contains outage or multi-user impact signals
- a billing discrepancy appears to be greater than $500
"""

import re
from typing import List

from app.schemas import (
    AIAnalysisResult,
    DestinationQueue,
    EscalationResult,
    RequestCategory,
    RoutingResult,
)


CONFIDENCE_THRESHOLD = 0.70
BILLING_DISCREPANCY_THRESHOLD = 500.0


OUTAGE_KEYWORDS = [
    "outage",
    "down",
    "stopped loading",
    "not loading",
    "unavailable",
    "service unavailable",
    "platform down",
    "dashboard down",
    "cannot access",
    "can't access",
    "not working",
]

MULTI_USER_KEYWORDS = [
    "multiple users",
    "all users",
    "entire team",
    "everyone",
    "company-wide",
    "across regions",
    "all our users",
]


# Extract numeric money values from strings such as "$1,240" or "$980/month".
def _extract_money_values(monetary_amounts: List[str]) -> List[float]:
    values = []

    for amount in monetary_amounts:
        cleaned_amount = amount.replace(",", "")

        matches = re.findall(r"\d+(?:\.\d+)?", cleaned_amount)

        for match in matches:
            try:
                values.append(float(match))
            except ValueError:
                continue

    return values


# Check if a billing message contains a discrepancy greater than the threshold.
def _has_large_billing_discrepancy(ai_analysis: AIAnalysisResult) -> bool:
    if ai_analysis.category != RequestCategory.BILLING_ISSUE:
        return False

    money_values = _extract_money_values(
        ai_analysis.extracted_entities.monetary_amounts
    )

    if len(money_values) < 2:
        return False

    discrepancy = max(money_values) - min(money_values)

    return discrepancy > BILLING_DISCREPANCY_THRESHOLD


# Check whether the raw message contains any escalation keywords.
def _contains_any_keyword(raw_message: str, keywords: List[str]) -> bool:
    normalized_message = raw_message.lower()

    return any(keyword in normalized_message for keyword in keywords)


# Decide if the request needs human review.
def evaluate_escalation(
    raw_message: str,
    ai_analysis: AIAnalysisResult,
    routing_result: RoutingResult,
) -> EscalationResult:
    """
    Evaluate whether a request should be escalated to human review.
    """

    escalation_reasons = []

    if ai_analysis.confidence_score < CONFIDENCE_THRESHOLD:
        escalation_reasons.append(
            f"LLM confidence is below {CONFIDENCE_THRESHOLD:.0%}."
        )

    if ai_analysis.category == RequestCategory.INCIDENT_OUTAGE:
        escalation_reasons.append(
            "Request is classified as an incident or outage."
        )

    if _contains_any_keyword(raw_message, OUTAGE_KEYWORDS):
        escalation_reasons.append(
            "Message contains outage or service-impact language."
        )

    if _contains_any_keyword(raw_message, MULTI_USER_KEYWORDS):
        escalation_reasons.append(
            "Message indicates multiple users or a wider team may be affected."
        )

    if _has_large_billing_discrepancy(ai_analysis):
        escalation_reasons.append(
            f"Billing discrepancy appears greater than ${BILLING_DISCREPANCY_THRESHOLD:.0f}."
        )

    human_escalation_required = len(escalation_reasons) > 0

    return EscalationResult(
        human_escalation_required=human_escalation_required,
        escalation_reasons=escalation_reasons,
    )


# Decide the final queue after escalation is evaluated.
def resolve_final_destination(
    routing_result: RoutingResult,
    escalation_result: EscalationResult,
) -> DestinationQueue:
    """
    Return Human Escalation Queue if escalation is required.
    Otherwise, keep the normal routing destination.
    """

    if escalation_result.human_escalation_required:
        return DestinationQueue.HUMAN_ESCALATION

    return routing_result.destination_queue