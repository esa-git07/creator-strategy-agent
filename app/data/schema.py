"""
Schema definitions for historical creator content records.

This module provides data models, expected column lists, and type mappings
used for ingesting, validating, and structuring historical creator content CSV files.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Set, Type, Union

# Union type for date fields (supports date, datetime, or ISO date string)
DateLike = Union[date, datetime, str]

# Canonical ordered list of all CSV columns
CSV_COLUMNS: List[str] = [
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
    "audience_feedback",
    "creator_notes",
]

# Set of required column names for completeness checks in loaders
REQUIRED_COLUMNS: Set[str] = set(CSV_COLUMNS)

# Type mapping for column parsing and validation
FIELD_TYPES: Dict[str, Type] = {
    "content_id": str,
    "creator_id": str,
    "date": DateLike,
    "platform": str,
    "title": str,
    "topic": str,
    "format": str,
    "hook": str,
    "views": int,
    "likes": int,
    "comments": int,
    "shares": int,
    "saves": int,
    "engagement_rate": float,
    "audience_feedback": str,
    "creator_notes": str,
}

# Categorized column groupings for type-casting in future CSV loaders
INTEGER_COLUMNS: List[str] = [
    "views",
    "likes",
    "comments",
    "shares",
    "saves",
]

FLOAT_COLUMNS: List[str] = [
    "engagement_rate",
]

NUMERIC_COLUMNS: List[str] = INTEGER_COLUMNS + FLOAT_COLUMNS

TEXT_COLUMNS: List[str] = [
    "content_id",
    "creator_id",
    "platform",
    "title",
    "topic",
    "format",
    "hook",
    "audience_feedback",
    "creator_notes",
]

DATE_COLUMNS: List[str] = [
    "date",
]


@dataclass
class ContentRecord:
    """
    Represents a single historical content item from a creator.
    """
    content_id: str
    creator_id: str
    date: DateLike
    platform: str
    title: str
    topic: str
    format: str
    hook: str
    views: int
    likes: int
    comments: int
    shares: int
    saves: int
    engagement_rate: float
    audience_feedback: str
    creator_notes: str
