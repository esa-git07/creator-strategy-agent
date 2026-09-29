# """
# Ingestion layer for creator history CSV into Hindsight persistent memory.
# """

import sys
from pathlib import Path
from typing import Dict, List

from app.data.loader import load_content_csv
from app.data.schema import ContentRecord
from app.memory.hindsight_client import get_hindsight_client, HindsightMemoryError


def _record_to_memory_text(record: ContentRecord) -> str:
    """Convert a ContentRecord into a detailed natural‑language description.

    The format is a multi‑line string that enumerates all fields for clarity.
    """
    parts = [
        f"Content ID: {record.content_id}",
        f"Creator ID: {record.creator_id}",
        f"Date: {record.date}",
        f"Platform: {record.platform}",
        f"Title: {record.title}",
        f"Topic: {record.topic}",
        f"Format: {record.format}",
        f"Hook: {record.hook}",
        f"Views: {record.views}, Likes: {record.likes}, Comments: {record.comments}, Shares: {record.shares}, Saves: {record.saves}",
        f"Engagement Rate: {record.engagement_rate}%",
        f"Audience Feedback: {record.audience_feedback}",
        f"Creator Notes: {record.creator_notes}",
    ]
    return "\n".join(parts)


def ingest_creator_history(
    csv_path: str | Path = "data/sample/creator_history.csv",
    bank_id: str = "creator_ai_001",
) -> Dict[str, List[Dict]]:
    """Load the CSV, transform each record into a memory string, and retain it.

    Returns a summary dictionary with two keys:
    * "retained": list of dicts for successfully retained memories
    * "skipped": list of dicts for records that were already present
    * "failed": list of dicts for records that raised an exception during retain
    """
    client = get_hindsight_client()
    # Resolve CSV path relative to the repository root.
    csv_path_obj = Path(csv_path)
    if not csv_path_obj.is_absolute():
        # The repository root is the workspace directory.
        csv_path_obj = Path.cwd() / csv_path_obj

    records: List[ContentRecord] = load_content_csv(csv_path_obj)
    summary = {"retained": [], "skipped": [], "failed": []}

    for rec in records:
        memory_text = _record_to_memory_text(rec)
        # Simple duplicate check – query the bank for the unique content_id.
        try:
            existing = client.recall_memories(
                bank_id=bank_id,
                query=rec.content_id,
                max_tokens=10,
            )
        except Exception:
            # If recall fails we treat it as no duplicate to avoid blocking ingestion.
            existing = []

        if any(
            (item.get("metadata") or {}).get("content_id") == rec.content_id
            or rec.content_id in (item.get("text") or "")
            for item in existing
        ):
            summary["skipped"].append({"content_id": rec.content_id})
            continue

        try:
            retain_res = client.retain_memory(
                bank_id=bank_id,
                content=memory_text,
                metadata={"content_id": rec.content_id, "date": str(rec.date)},
            )
            summary["retained"].append({"content_id": rec.content_id, **retain_res})
        except HindsightMemoryError as e:
            summary["failed"].append({"content_id": rec.content_id, "error": str(e)})
        except Exception as e:
            summary["failed"].append({"content_id": rec.content_id, "error": str(e)})

    return summary


if __name__ == "__main__":
    # Simple command‑line execution for manual runs.
    result = ingest_creator_history()
    print("Ingestion summary:")
    print(result)
    sys.exit(0)
