"""
main.py

FastAPI backend for the ArcVault AI triage workflow.

This API exposes endpoints to:
- process one customer request
- process the five assessment sample requests
- read saved output records
- clear saved output records

FastAPI is used to simulate a production-style intake API/webhook endpoint.
"""

from fastapi import FastAPI, HTTPException

from app.graph import process_request
from app.persistence import clear_processed_records, read_processed_records
from app.sample_data import SAMPLE_REQUESTS
from app.schemas import (
    BatchTriageResponse,
    CustomerRequest,
    SingleTriageResponse,
)


app = FastAPI(
    title="ArcVault AI Intake & Triage API",
    description=(
        "AI-powered workflow for customer request classification, enrichment, "
        "routing, escalation, and structured output generation."
    ),
    version="1.0.0",
)


@app.get("/health")
def health_check():
    """
    Simple health check endpoint.

    Used to confirm that the FastAPI server is running.
    """
    return {
        "status": "ok",
        "service": "ArcVault AI Intake & Triage API",
    }


@app.post("/triage", response_model=SingleTriageResponse)
def triage_single_request(request: CustomerRequest):
    """
    Process one inbound customer request through the LangGraph workflow.
    """
    try:
        record = process_request(request)

        return SingleTriageResponse(
            success=True,
            record=record,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process request: {str(exc)}",
        ) from exc


@app.post("/triage/samples", response_model=BatchTriageResponse)
def triage_sample_requests():
    """
    Process the five sample requests from the assessment.

    The output file is cleared first so the batch run produces a clean result set.
    """
    try:
        clear_processed_records()

        records = [process_request(request) for request in SAMPLE_REQUESTS]

        return BatchTriageResponse(
            success=True,
            total_processed=len(records),
            records=records,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process sample requests: {str(exc)}",
        ) from exc


@app.get("/results")
def get_results():
    """
    Return all records currently saved in outputs/processed_requests.json.
    """
    try:
        return {
            "success": True,
            "total_records": len(read_processed_records()),
            "records": read_processed_records(),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read results: {str(exc)}",
        ) from exc


@app.delete("/results")
def clear_results():
    """
    Clear all saved output records.
    """
    try:
        clear_processed_records()

        return {
            "success": True,
            "message": "Processed records cleared successfully.",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear results: {str(exc)}",
        ) from exc