"""
streamlit_app.py

Lightweight Streamlit demo for the ArcVault AI triage workflow.

This UI is intentionally simple:
- FastAPI remains the backend workflow service.
- Streamlit is only used as a reviewer-friendly demo interface.

Architecture:
Streamlit -> FastAPI -> LangGraph -> Groq -> JSON output
"""

import json
from typing import Any, Dict, Optional

import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="ArcVault AI Workflow",
    page_icon="🧭",
    layout="wide",
)


def call_api(
    method: str,
    endpoint: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Call the FastAPI backend and return the JSON response."""
    url = f"{API_BASE_URL}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, timeout=180)
        elif method == "POST":
            response = requests.post(url, json=payload, timeout=180)
        elif method == "DELETE":
            response = requests.delete(url, timeout=180)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as exc:
        st.error(f"Could not reach the FastAPI backend: {exc}")
        st.info("Run this first: uvicorn app.main:app --reload --port 8000")
        return None


def record_to_row(record: Dict[str, Any]) -> Dict[str, Any]:
    """Convert one processed record into a simple table row."""
    return {
        "ID": record.get("request_id"),
        "Category": record.get("category"),
        "Priority": record.get("priority"),
        "Confidence": record.get("confidence_score"),
        "Urgency": record.get("urgency_signal"),
        "Queue": record.get("destination_queue"),
        "Escalated": "Yes" if record.get("human_escalation_required") else "No",
        "Core Issue": record.get("core_issue"),
    }


def priority_badge(priority: str) -> str:
    """Return a visual badge for the priority level."""
    badges = {
        "High": "🔴 High",
        "Medium": "🟡 Medium",
        "Low": "🟢 Low",
    }
    return badges.get(priority, priority or "N/A")


def urgency_badge(urgency: str) -> str:
    """Return a visual badge for the urgency signal."""
    badges = {
        "High": "🔴 High",
        "Medium": "🟡 Medium",
        "Low": "🟢 Low",
    }
    return badges.get(urgency, urgency or "N/A")


def queue_badge(queue: str) -> str:
    """Return a visual label for the destination queue."""
    icons = {
        "Engineering Queue": "⚙️ Engineering Queue",
        "Product Queue": "📦 Product Queue",
        "Billing Queue": "💳 Billing Queue",
        "IT/Security Queue": "🔒 IT/Security Queue",
        "Human Escalation Queue": "🚨 Human Escalation Queue",
    }
    return icons.get(queue, queue or "N/A")


def show_record(record: Dict[str, Any]) -> None:
    """Display one processed triage record in a clean, visual format."""
    st.markdown("### Triage Decision")

    category = record.get("category", "N/A")
    priority = record.get("priority", "N/A")
    confidence = record.get("confidence_score", "N/A")
    urgency = record.get("urgency_signal", "N/A")
    queue = record.get("destination_queue", "N/A")
    escalated = record.get("human_escalation_required", False)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Category", category)
    col2.metric("Priority", priority_badge(priority))
    col3.metric("Confidence", confidence)
    col4.metric("Urgency", urgency_badge(urgency))

    st.markdown("### Routing Outcome")

    if escalated:
        st.error("🚨 Human escalation required")
    else:
        st.success("✅ Routed to standard destination")

    st.markdown(
        f"""
        **Destination Queue:** {queue_badge(queue)}  
        **Routing Reason:** {record.get("routing_reason", "N/A")}
        """
    )

    if escalated:
        st.markdown("#### Escalation Reasons")
        for reason in record.get("escalation_reasons", []):
            st.warning(reason)

    st.markdown("### Request Understanding")

    st.markdown("#### Core Issue")
    st.write(record.get("core_issue", "N/A"))

    st.markdown("#### Summary for Receiving Team")
    st.write(record.get("summary", "N/A"))

    with st.expander("Extracted Entities", expanded=True):
        entities = record.get("extracted_entities", {})
        st.json(entities)

    with st.expander("Technical Metadata", expanded=False):
        st.write(f"**Model Provider:** {record.get('model_provider', 'N/A')}")
        st.write(f"**Model Name:** {record.get('model_name', 'N/A')}")
        st.write(f"**Workflow Version:** {record.get('workflow_version', 'N/A')}")
        st.write(f"**Processing Time:** {record.get('processing_duration_ms', 'N/A')} ms")

    with st.expander("Full JSON Record", expanded=False):
        st.json(record)


st.title("🧭 ArcVault AI Workflow Console")
st.caption(
    "A lightweight demo for automated intake, classification, enrichment, routing, and escalation."
)

with st.sidebar:
    st.header("Backend Connection")

    health = call_api("GET", "/health")

    if health:
        st.success("FastAPI backend connected")
        st.caption(f"Service: {health.get('service', 'ArcVault API')}")
        st.link_button("Open FastAPI Docs", f"{API_BASE_URL}/docs")
    else:
        st.error("FastAPI backend is not available")
        st.caption("Start the backend service before running requests.")

tab_console, tab_samples = st.tabs(
    [
        "Triage Console",
        "Sample Batch & Results",
    ]
)


with tab_console:
    left, right = st.columns([1, 1.2])

    with left:
        st.subheader("New Customer Request")

        source = st.selectbox(
            "Source",
            ["Email", "Web Form", "Support Portal", "Webhook", "Manual Entry"],
        )

        raw_message = st.text_area(
            "Raw message",
            height=220,
            placeholder="Paste an inbound customer request here...",
        )

        run_single = st.button("Run Triage", type="primary", use_container_width=True)

    with right:
        if run_single:
            if not raw_message.strip():
                st.warning("Please enter a message first.")
            else:
                payload = {
                    "source": source,
                    "raw_message": raw_message,
                }

                with st.spinner("Processing through FastAPI + LangGraph + Groq..."):
                    result = call_api("POST", "/triage", payload)

                if result:
                    show_record(result["record"])
        else:
            st.info("Enter a customer request on the left, then click Run Triage.")


with tab_samples:
    st.subheader("Assessment Sample Run")

    st.write(
        "Run the five required ArcVault sample inputs and inspect the structured output."
    )

    col_run, col_clear = st.columns(2)

    with col_run:
        run_batch = st.button("Run 5 Sample Requests", type="primary", use_container_width=True)

    with col_clear:
        clear_results = st.button("Clear Saved Results", use_container_width=True)

    if clear_results:
        result = call_api("DELETE", "/results")
        if result:
            st.success("Saved records cleared.")

    if run_batch:
        with st.spinner("Processing all five sample requests..."):
            result = call_api("POST", "/triage/samples")

        if result:
            st.success(f"Processed {result['total_processed']} requests.")

    results = call_api("GET", "/results")

    if results and results.get("records"):
        records = results["records"]
        rows = [record_to_row(record) for record in records]

        st.markdown("### Output Table")
        st.dataframe(rows, use_container_width=True)

        st.download_button(
            label="Download JSON Output",
            data=json.dumps(records, indent=2, ensure_ascii=False),
            file_name="processed_requests.json",
            mime="application/json",
            use_container_width=True,
        )

        st.markdown("### Inspect One Record")
        selected_id = st.selectbox(
            "Select request",
            [record["request_id"] for record in records],
        )

        selected_record = next(
            record for record in records if record["request_id"] == selected_id
        )

        show_record(selected_record)

    else:
        st.info("No saved records yet. Run the sample batch first.")