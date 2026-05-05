"""
persistence.py

Handles reading and writing processed triage records to a JSON file.

The assessment requires a structured output file containing the processed records.
For this project, we use a local JSON file as the persistent destination.

In production, this layer could be replaced with a database, Google Sheets,
a ticketing system, or a webhook integration.
"""

import json
from pathlib import Path
from typing import List

from app.schemas import ProcessedTriageRecord


# Path where processed records will be saved.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE_PATH = PROJECT_ROOT / "outputs" / "processed_requests.json"

# Ensure the outputs folder and JSON file exist before writing.
def ensure_output_file_exists() -> None:
    OUTPUT_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not OUTPUT_FILE_PATH.exists():
        OUTPUT_FILE_PATH.write_text("[]", encoding="utf-8")


# Read all processed records from the JSON output file.
def read_processed_records() -> List[dict]:
    ensure_output_file_exists()

    try:
        file_content = OUTPUT_FILE_PATH.read_text(encoding="utf-8").strip()

        if not file_content:
            return []

        records = json.loads(file_content)

        if not isinstance(records, list):
            raise ValueError("Output file must contain a JSON list.")

        return records

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Could not read {OUTPUT_FILE_PATH}. The file contains invalid JSON."
        ) from exc


# Write all records back to the JSON output file.
def write_processed_records(records: List[dict]) -> None:
    ensure_output_file_exists()

    OUTPUT_FILE_PATH.write_text(
        json.dumps(records, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


# Append one processed triage record to the JSON output file.
def append_processed_record(record: ProcessedTriageRecord) -> None:
    records = read_processed_records()

    records.append(record.model_dump(mode="json"))

    write_processed_records(records)


# Clear the output file before a fresh batch run.
def clear_processed_records() -> None:
    write_processed_records([])