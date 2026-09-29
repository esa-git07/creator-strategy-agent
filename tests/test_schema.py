import unittest
from datetime import date
from app.data.schema import (
    CSV_COLUMNS,
    REQUIRED_COLUMNS,
    FIELD_TYPES,
    NUMERIC_COLUMNS,
    INTEGER_COLUMNS,
    FLOAT_COLUMNS,
    TEXT_COLUMNS,
    DATE_COLUMNS,
    ContentRecord,
)


class TestContentSchema(unittest.TestCase):
    def test_schema_column_count_and_order(self):
        expected_columns = [
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
        self.assertEqual(CSV_COLUMNS, expected_columns)
        self.assertEqual(len(CSV_COLUMNS), 16)

    def test_required_columns_and_field_types(self):
        self.assertEqual(REQUIRED_COLUMNS, set(CSV_COLUMNS))
        self.assertEqual(set(FIELD_TYPES.keys()), set(CSV_COLUMNS))

    def test_column_groupings(self):
        self.assertEqual(set(NUMERIC_COLUMNS), set(INTEGER_COLUMNS + FLOAT_COLUMNS))
        self.assertEqual(len(INTEGER_COLUMNS), 5)
        self.assertEqual(len(FLOAT_COLUMNS), 1)
        self.assertEqual(len(DATE_COLUMNS), 1)
        all_grouped = set(NUMERIC_COLUMNS) | set(TEXT_COLUMNS) | set(DATE_COLUMNS)
        self.assertEqual(all_grouped, set(CSV_COLUMNS))

    def test_content_record_instantiation(self):
        record = ContentRecord(
            content_id="post_001",
            creator_id="creator_123",
            date=date(2026, 1, 15),
            platform="YouTube",
            title="How to Build an AI Agent",
            topic="AI Engineering",
            format="Long-form Video",
            hook="Most developers build AI agents the wrong way.",
            views=15000,
            likes=1200,
            comments=85,
            shares=140,
            saves=450,
            engagement_rate=0.125,
            audience_feedback="Loved the architectural diagram at 03:20",
            creator_notes="First video using the new microphone setup.",
        )
        self.assertEqual(record.content_id, "post_001")
        self.assertEqual(record.views, 15000)
        self.assertEqual(record.engagement_rate, 0.125)


if __name__ == "__main__":
    unittest.main()
