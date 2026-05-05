"""
graph.py

Builds the LangGraph workflow for the ArcVault AI triage pipeline.

The graph processes one customer request through these steps:
1. Initialize request metadata
2. Classify and enrich the request using the LLM
3. Route the request using deterministic business rules
4. Evaluate human escalation rules
5. Build and save the final structured record

LangGraph is used because this is a multi-step workflow where each step adds
new information to a shared state object.
"""

import time
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.escalation import evaluate_escalation, resolve_final_destination
from app.llm_client import analyze_request_with_llm, get_model_name, get_model_provider
from app.persistence import append_processed_record
from app.routing import route_request
from app.schemas import ProcessedTriageRecord
from app.state import TriageWorkflowState


# Initialize timing, request ID, and model metadata.
def initialize_request_node(state: TriageWorkflowState) -> TriageWorkflowState:
    incoming_request = state["incoming_request"]

    if incoming_request.request_id is None:
        incoming_request.request_id = f"REQ-{uuid4().hex[:8].upper()}"

    return {
        **state,
        "incoming_request": incoming_request,
        "started_at_ms": int(time.time() * 1000),
        "model_provider": get_model_provider(),
        "model_name": get_model_name(),
    }


# Run LLM classification and enrichment.
def analyze_with_llm_node(state: TriageWorkflowState) -> TriageWorkflowState:
    incoming_request = state["incoming_request"]

    ai_analysis = analyze_request_with_llm(incoming_request)

    return {
        **state,
        "ai_analysis": ai_analysis,
    }


# Apply deterministic routing based on the LLM category.
def route_request_node(state: TriageWorkflowState) -> TriageWorkflowState:
    ai_analysis = state["ai_analysis"]

    if ai_analysis is None:
        raise ValueError("Cannot route request because ai_analysis is missing.")

    routing_result = route_request(ai_analysis)

    return {
        **state,
        "routing_result": routing_result,
    }


# Evaluate whether the request needs human review.
def evaluate_escalation_node(state: TriageWorkflowState) -> TriageWorkflowState:
    incoming_request = state["incoming_request"]
    ai_analysis = state["ai_analysis"]
    routing_result = state["routing_result"]

    if ai_analysis is None:
        raise ValueError("Cannot evaluate escalation because ai_analysis is missing.")

    if routing_result is None:
        raise ValueError("Cannot evaluate escalation because routing_result is missing.")

    escalation_result = evaluate_escalation(
        raw_message=incoming_request.raw_message,
        ai_analysis=ai_analysis,
        routing_result=routing_result,
    )

    return {
        **state,
        "escalation_result": escalation_result,
    }


# Build the final record, apply escalation destination override, and save it.
def finalize_and_save_record_node(state: TriageWorkflowState) -> TriageWorkflowState:
    incoming_request = state["incoming_request"]
    ai_analysis = state["ai_analysis"]
    routing_result = state["routing_result"]
    escalation_result = state["escalation_result"]

    if ai_analysis is None:
        raise ValueError("Cannot finalize record because ai_analysis is missing.")

    if routing_result is None:
        raise ValueError("Cannot finalize record because routing_result is missing.")

    if escalation_result is None:
        raise ValueError("Cannot finalize record because escalation_result is missing.")

    started_at_ms = state.get("started_at_ms") or int(time.time() * 1000)
    finished_at_ms = int(time.time() * 1000)
    processing_duration_ms = finished_at_ms - started_at_ms

    final_destination = resolve_final_destination(
        routing_result=routing_result,
        escalation_result=escalation_result,
    )

    final_record = ProcessedTriageRecord(
        request_id=incoming_request.request_id or f"REQ-{uuid4().hex[:8].upper()}",
        source=incoming_request.source,
        raw_message=incoming_request.raw_message,
        category=ai_analysis.category,
        priority=ai_analysis.priority,
        confidence_score=ai_analysis.confidence_score,
        core_issue=ai_analysis.core_issue,
        extracted_entities=ai_analysis.extracted_entities,
        urgency_signal=ai_analysis.urgency_signal,
        summary=ai_analysis.summary,
        destination_queue=final_destination,
        routing_reason=routing_result.routing_reason,
        human_escalation_required=escalation_result.human_escalation_required,
        escalation_reasons=escalation_result.escalation_reasons,
        model_provider=state.get("model_provider") or "unknown",
        model_name=state.get("model_name") or "unknown",
        workflow_version="1.0",
        processing_duration_ms=processing_duration_ms,
    )

    append_processed_record(final_record)

    return {
        **state,
        "final_record": final_record,
    }


# Build and compile the LangGraph workflow.
def build_graph():
    workflow = StateGraph(TriageWorkflowState)

    workflow.add_node("initialize_request", initialize_request_node)
    workflow.add_node("analyze_with_llm", analyze_with_llm_node)
    workflow.add_node("route_request", route_request_node)
    workflow.add_node("evaluate_escalation", evaluate_escalation_node)
    workflow.add_node("finalize_and_save_record", finalize_and_save_record_node)

    workflow.add_edge(START, "initialize_request")
    workflow.add_edge("initialize_request", "analyze_with_llm")
    workflow.add_edge("analyze_with_llm", "route_request")
    workflow.add_edge("route_request", "evaluate_escalation")
    workflow.add_edge("evaluate_escalation", "finalize_and_save_record")
    workflow.add_edge("finalize_and_save_record", END)

    return workflow.compile()


# Compiled graph used by FastAPI, Streamlit, and local tests.
graph = build_graph()


# Helper function for processing one request from outside the graph.
def process_request(incoming_request):
    result_state = graph.invoke(
        {
            "incoming_request": incoming_request,
        }
    )

    return result_state["final_record"]