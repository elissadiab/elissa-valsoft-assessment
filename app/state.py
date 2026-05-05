"""
state.py

This file defines the shared workflow state used by LangGraph.

The state works like a temporary memory for one customer request.
Each node in the workflow reads data from the state, adds its own result,
and passes the updated state to the next node.

For example:
- The workflow starts with an incoming customer request.
- The AI node adds the classification and extracted information.
- The routing node adds the destination queue.
- The escalation node adds whether human review is needed.
- The final node creates the complete output record.
"""

from typing import Optional, TypedDict

from app.schemas import (
    AIAnalysisResult,
    CustomerRequest,
    EscalationResult,
    ProcessedTriageRecord,
    RoutingResult,
)


class TriageWorkflowState(TypedDict, total=False):
    """
    Shared state for processing one ArcVault customer request.
    """

    # Set before the workflow starts.
    incoming_request: CustomerRequest

    # Set by the timing/ingestion step.
    started_at_ms: Optional[int]

    # Set by the LLM analysis node.
    ai_analysis: Optional[AIAnalysisResult]

    # Set by the deterministic routing node.
    routing_result: Optional[RoutingResult]

    # Set by the escalation rules node.
    escalation_result: Optional[EscalationResult]

    # Set by the finalization/persistence node.
    final_record: Optional[ProcessedTriageRecord]

    # Used for output metadata.
    model_provider: Optional[str]
    model_name: Optional[str]