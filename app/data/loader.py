"""
CSV loading and validation layer for historical creator content records.

This module parses CSV files or streams, validates them against the schema
defined in app.data.schema, and constructs validated ContentRecord objects.
"""

import csv
import io
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TextIO, Union

from app.data.schema import (
    CSV_COLUMNS,
    FLOAT_COLUMNS,
    INTEGER_COLUMNS,
    REQUIRED_COLUMNS,
    ContentRecord,
)

# Fields that must have non-empty values for a ContentRecord to be usable.
# Core identifiers, publication metadata, and metrics are strictly required.
REQUIRED_VALUE_FIELDS: Set[str] = {
    "content_id",
    "creator_id",
    "date",
    "platform",
    "title",
    "topic",
    "format",
    "hook",
    "views",
    "likes",
    "comments",
    "shares",
    "saves",
    "engagement_rate",
}


class CSVValidationError(ValueError):
    """
    Raised when CSV structure, headers, or row data fail validation.
    """

    def __init__(
        self,
        message: str,
        row: Optional[int] = None,
        column: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.row = row
        self.column = column

    def __str__(self) -> str:
        return self.message


def parse_date(value: str, row_num: int) -> date:
    """
    Parse a date string into a datetime.date object.
    Supports ISO format (YYYY-MM-DD) and common variants.
    """
    clean_val = value.strip() if value else ""
    if not clean_val:
        raise CSVValidationError(
            f"Row {row_num}: Field 'date' cannot be empty.",
            row=row_num,
            column="date",
        )

    # Standard ISO 8601 (YYYY-MM-DD)
    try:
        return date.fromisoformat(clean_val)
    except ValueError:
        pass

    # Common date formats
    for fmt in ("%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(clean_val, fmt).date()
        except ValueError:
            pass

    # DateTime with timestamp
    try:
        return datetime.fromisoformat(clean_val).date()
    except ValueError:
        pass

    raise CSVValidationError(
        f"Row {row_num}: Invalid date for 'date': '{clean_val}'. Expected format YYYY-MM-DD.",
        row=row_num,
        column="date",
    )


def parse_int(value: str, field_name: str, row_num: int) -> int:
    """
    Parse a non-negative integer string.
    """
    clean_val = value.strip() if value else ""
    if not clean_val:
        raise CSVValidationError(
            f"Row {row_num}: Field '{field_name}' cannot be empty.",
            row=row_num,
            column=field_name,
        )

    try:
        val = int(clean_val)
    except ValueError:
        raise CSVValidationError(
            f"Row {row_num}: Invalid integer for '{field_name}': '{clean_val}'.",
            row=row_num,
            column=field_name,
        )

    if val < 0:
        raise CSVValidationError(
            f"Row {row_num}: Field '{field_name}' cannot be negative: {val}.",
            row=row_num,
            column=field_name,
        )

    return val


def parse_float(value: str, field_name: str, row_num: int) -> float:
    """
    Parse a non-negative floating point number.
    """
    clean_val = value.strip() if value else ""
    if not clean_val:
        raise CSVValidationError(
            f"Row {row_num}: Field '{field_name}' cannot be empty.",
            row=row_num,
            column=field_name,
        )

    try:
        val = float(clean_val)
    except ValueError:
        raise CSVValidationError(
            f"Row {row_num}: Invalid float for '{field_name}': '{clean_val}'.",
            row=row_num,
            column=field_name,
        )

    if math.isnan(val) or math.isinf(val):
        raise CSVValidationError(
            f"Row {row_num}: Invalid numeric value for '{field_name}': '{clean_val}'.",
            row=row_num,
            column=field_name,
        )

    if val < 0.0:
        raise CSVValidationError(
            f"Row {row_num}: Field '{field_name}' cannot be negative: {val}.",
            row=row_num,
            column=field_name,
        )

    return val


def _parse_csv_stream(stream: TextIO) -> List[ContentRecord]:
    """
    Internal helper to parse and validate rows from a text stream.
    """
    reader = csv.DictReader(stream)

    if reader.fieldnames is None:
        raise CSVValidationError("CSV file is empty or missing a header row.")

    # Safely strip whitespace from column headers
    cleaned_fieldnames = [
        col.strip() for col in reader.fieldnames if col is not None
    ]

    # Verify that all required columns from schema.py exist
    missing_columns = [
        col for col in CSV_COLUMNS if col not in cleaned_fieldnames
    ]
    if missing_columns:
        raise CSVValidationError(
            f"CSV is missing required column(s): {', '.join(missing_columns)}"
        )

    # Reassign cleaned fieldnames so DictReader keys match stripped column names
    reader.fieldnames = cleaned_fieldnames

    records: List[ContentRecord] = []

    # Start enumerate at 2 since line 1 is the CSV header
    for row_idx, row in enumerate(reader, start=2):
        # Ignore completely empty rows or trailing blank lines
        if not row or not any(
            v is not None and v.strip() != "" for v in row.values()
        ):
            continue

        # Check for missing required values
        for col in REQUIRED_VALUE_FIELDS:
            val = row.get(col)
            if val is None or val.strip() == "":
                raise CSVValidationError(
                    f"Row {row_idx}: Missing required value for '{col}'.",
                    row=row_idx,
                    column=col,
                )

        # Parse date
        raw_date = row.get("date", "")
        parsed_date = parse_date(raw_date, row_num=row_idx)

        # Parse integer metrics
        parsed_ints = {}
        for col in INTEGER_COLUMNS:
            raw_val = row.get(col, "")
            parsed_ints[col] = parse_int(raw_val, field_name=col, row_num=row_idx)

        # Parse float metric
        raw_rate = row.get("engagement_rate", "")
        parsed_rate = parse_float(
            raw_rate, field_name="engagement_rate", row_num=row_idx
        )

        # Safely preserve text fields with whitespace trimmed
        content_id = (row.get("content_id") or "").strip()
        creator_id = (row.get("creator_id") or "").strip()
        platform = (row.get("platform") or "").strip()
        title = (row.get("title") or "").strip()
        topic = (row.get("topic") or "").strip()
        format_ = (row.get("format") or "").strip()
        hook = (row.get("hook") or "").strip()
        audience_feedback = (row.get("audience_feedback") or "").strip()
        creator_notes = (row.get("creator_notes") or "").strip()

        record = ContentRecord(
            content_id=content_id,
            creator_id=creator_id,
            date=parsed_date,
            platform=platform,
            title=title,
            topic=topic,
            format=format_,
            hook=hook,
            views=parsed_ints["views"],
            likes=parsed_ints["likes"],
            comments=parsed_ints["comments"],
            shares=parsed_ints["shares"],
            saves=parsed_ints["saves"],
            engagement_rate=parsed_rate,
            audience_feedback=audience_feedback,
            creator_notes=creator_notes,
        )
        records.append(record)

    return records


def load_content_csv(
    source: Union[str, Path, TextIO],
) -> List[ContentRecord]:
    """
    Loads historical creator content from a CSV source, validates all fields
    against the schema, and returns a list of ContentRecord instances.

    Parameters:
        source: File path (str or Path), raw CSV string with newlines, or file-like stream.

    Returns:
        List[ContentRecord]: List of validated content records.

    Raises:
        CSVValidationError: If columns are missing or values fail validation.
        FileNotFoundError: If the specified file path does not exist.
    """
    if isinstance(source, Path):
        if not source.exists():
            raise FileNotFoundError(f"CSV file not found: {source}")
        with source.open("r", encoding="utf-8-sig", newline="") as f:
            return _parse_csv_stream(f)

    if isinstance(source, str):
        # If it contains newline characters, treat it directly as in-memory CSV text
        if "\n" in source or "\r" in source:
            return _parse_csv_stream(io.StringIO(source))

        path = Path(source)
        if path.exists():
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                return _parse_csv_stream(f)

        if source.lower().endswith(".csv"):
            raise FileNotFoundError(f"CSV file not found: {source}")

        return _parse_csv_stream(io.StringIO(source))

    if hasattr(source, "read"):
        # Check if the stream yields bytes instead of strings
        if hasattr(source, "seek"):
            try:
                source.seek(0)
            except Exception:
                pass
        sample = source.read(1024)
        if hasattr(source, "seek"):
            try:
                source.seek(0)
            except Exception:
                pass

        if isinstance(sample, bytes):
            raw_content = source.read()
            text = raw_content.decode("utf-8-sig")
            return _parse_csv_stream(io.StringIO(text))

        return _parse_csv_stream(source)

    raise ValueError(f"Unsupported source type: {type(source)}")
