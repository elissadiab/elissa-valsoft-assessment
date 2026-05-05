"""
routing.py

Contains deterministic routing logic for the ArcVault triage workflow.

The LLM is responsible for understanding and classifying the customer message.
This file is responsible for mapping the classification result to the correct
internal destination queue.

Keeping routing outside the LLM makes the workflow easier to audit, test, and change.
"""

from app.schemas import (
    AIAnalysisResult,
    DestinationQueue,
    RequestCategory,
    RoutingResult,
)


# Maps each request category to the default operational queue.
CATEGORY_TO_QUEUE = {
    RequestCategory.BUG_REPORT: DestinationQueue.ENGINEERING,
    RequestCategory.FEATURE_REQUEST: DestinationQueue.PRODUCT,
    RequestCategory.BILLING_ISSUE: DestinationQueue.BILLING,
    RequestCategory.TECHNICAL_QUESTION: DestinationQueue.IT_SECURITY,
    RequestCategory.INCIDENT_OUTAGE: DestinationQueue.ENGINEERING,
}


# Human-readable explanations for each routing decision.
CATEGORY_ROUTING_REASONS = {
    RequestCategory.BUG_REPORT: (
        "Bug reports are routed to Engineering because they may require code-level investigation."
    ),
    RequestCategory.FEATURE_REQUEST: (
        "Feature requests are routed to Product because they may affect roadmap planning and prioritization."
    ),
    RequestCategory.BILLING_ISSUE: (
        "Billing issues are routed to Billing because they involve invoices, charges, or contract rates."
    ),
    RequestCategory.TECHNICAL_QUESTION: (
        "Technical questions are routed to IT/Security because they often involve integrations, authentication, or configuration."
    ),
    RequestCategory.INCIDENT_OUTAGE: (
        "Incidents and outages are initially mapped to Engineering because they may require technical investigation."
    ),
}


# Builds the routing result from the LLM analysis result.
def route_request(ai_analysis: AIAnalysisResult) -> RoutingResult:
    """
    Determine the destination queue based on the classified category.

    Args:
        ai_analysis: Structured result produced by the LLM.

    Returns:
        RoutingResult containing the destination queue and routing explanation.

    Raises:
        ValueError: If the category cannot be mapped to a queue.
    """

    try:
        destination_queue = CATEGORY_TO_QUEUE[ai_analysis.category]
        routing_reason = CATEGORY_ROUTING_REASONS[ai_analysis.category]

        return RoutingResult(
            destination_queue=destination_queue,
            routing_reason=routing_reason,
        )

    except KeyError as exc:
        raise ValueError(
            f"No routing rule found for category: {ai_analysis.category}"
        ) from exc