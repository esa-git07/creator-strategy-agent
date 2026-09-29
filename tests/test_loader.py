import io
import unittest
from datetime import date
from app.data.loader import CSVValidationError, load_content_csv
from app.data.schema import CSV_COLUMNS


def make_csv_row(**kwargs) -> str:
    default_values = {
        "content_id": "post_001",
        "creator_id": "creator_123",
        "date": "2026-01-15",
        "platform": "YouTube",
        "title": "How to Build an AI Agent",
        "topic": "AI Engineering",
        "format": "Long-form Video",
        "hook": "Stop hardcoding your prompts.",
        "views": "15000",
        "likes": "1200",
        "comments": "85",
        "shares": "140",
        "saves": "450",
        "engagement_rate": "0.125",
        "audience_feedback": "Great breakdown of the memory layer.",
        "creator_notes": "First time testing chapters in description.",
    }
    default_values.update(kwargs)
    return ",".join(f'"{default_values[col]}"' for col in CSV_COLUMNS)


def make_csv_content(rows: list[str]) -> str:
    header = ",".join(CSV_COLUMNS)
    return header + "\n" + "\n".join(rows) + "\n"


class TestCSVLoader(unittest.TestCase):
    def test_valid_csv_loads_successfully(self):
        row_str = make_csv_row()
        csv_data = make_csv_content([row_str])

        records = load_content_csv(csv_data)
        self.assertEqual(len(records), 1)

        record = records[0]
        self.assertEqual(record.content_id, "post_001")
        self.assertEqual(record.creator_id, "creator_123")
        self.assertEqual(record.date, date(2026, 1, 15))
        self.assertEqual(record.platform, "YouTube")
        self.assertEqual(record.title, "How to Build an AI Agent")
        self.assertEqual(record.topic, "AI Engineering")
        self.assertEqual(record.format, "Long-form Video")
        self.assertEqual(record.hook, "Stop hardcoding your prompts.")
        self.assertEqual(record.views, 15000)
        self.assertEqual(record.likes, 1200)
        self.assertEqual(record.comments, 85)
        self.assertEqual(record.shares, 140)
        self.assertEqual(record.saves, 450)
        self.assertAlmostEqual(record.engagement_rate, 0.125)
        self.assertEqual(record.audience_feedback, "Great breakdown of the memory layer.")
        self.assertEqual(record.creator_notes, "First time testing chapters in description.")

    def test_missing_required_column_rejected(self):
        # CSV missing the "platform" column
        columns_without_platform = [c for c in CSV_COLUMNS if c != "platform"]
        header = ",".join(columns_without_platform)
        row = ",".join(['"val"' for _ in columns_without_platform])
        csv_data = f"{header}\n{row}\n"

        with self.assertRaises(CSVValidationError) as ctx:
            load_content_csv(csv_data)

        self.assertIn("missing required column", str(ctx.exception).lower())
        self.assertIn("platform", str(ctx.exception))

    def test_invalid_integer_rejected(self):
        # Invalid integer string for 'views'
        row_str = make_csv_row(views="not_a_number")
        csv_data = make_csv_content([row_str])

        with self.assertRaises(CSVValidationError) as ctx:
            load_content_csv(csv_data)

        self.assertIn("Invalid integer for 'views'", str(ctx.exception))
        self.assertEqual(ctx.exception.row, 2)
        self.assertEqual(ctx.exception.column, "views")

        # Negative integer for 'likes'
        row_negative = make_csv_row(likes="-10")
        csv_negative = make_csv_content([row_negative])

        with self.assertRaises(CSVValidationError) as ctx:
            load_content_csv(csv_negative)

        self.assertIn("cannot be negative", str(ctx.exception))
        self.assertEqual(ctx.exception.column, "likes")

    def test_invalid_float_rejected(self):
        # Non-numeric string for 'engagement_rate'
        row_str = make_csv_row(engagement_rate="high")
        csv_data = make_csv_content([row_str])

        with self.assertRaises(CSVValidationError) as ctx:
            load_content_csv(csv_data)

        self.assertIn("Invalid float for 'engagement_rate'", str(ctx.exception))
        self.assertEqual(ctx.exception.row, 2)
        self.assertEqual(ctx.exception.column, "engagement_rate")

        # Negative float for 'engagement_rate'
        row_neg = make_csv_row(engagement_rate="-0.05")
        csv_neg = make_csv_content([row_neg])

        with self.assertRaises(CSVValidationError) as ctx:
            load_content_csv(csv_neg)

        self.assertIn("cannot be negative", str(ctx.exception))
        self.assertEqual(ctx.exception.column, "engagement_rate")

    def test_invalid_date_rejected(self):
        # Invalid date format
        row_str = make_csv_row(date="invalid-date")
        csv_data = make_csv_content([row_str])

        with self.assertRaises(CSVValidationError) as ctx:
            load_content_csv(csv_data)

        self.assertIn("Invalid date for 'date'", str(ctx.exception))
        self.assertEqual(ctx.exception.row, 2)
        self.assertEqual(ctx.exception.column, "date")

        # Out-of-bounds calendar date
        row_oob = make_csv_row(date="2026-02-31")
        csv_oob = make_csv_content([row_oob])

        with self.assertRaises(CSVValidationError) as ctx:
            load_content_csv(csv_oob)

        self.assertIn("Invalid date for 'date'", str(ctx.exception))

    def test_missing_required_value_rejected(self):
        # Missing 'title'
        row_str = make_csv_row(title="")
        csv_data = make_csv_content([row_str])

        with self.assertRaises(CSVValidationError) as ctx:
            load_content_csv(csv_data)

        self.assertIn("Missing required value for 'title'", str(ctx.exception))
        self.assertEqual(ctx.exception.row, 2)
        self.assertEqual(ctx.exception.column, "title")

        # Missing 'content_id'
        row_no_id = make_csv_row(content_id="   ")
        csv_no_id = make_csv_content([row_no_id])

        with self.assertRaises(CSVValidationError) as ctx:
            load_content_csv(csv_no_id)

        self.assertIn("Missing required value for 'content_id'", str(ctx.exception))

    def test_multiple_valid_records_load_successfully(self):
        row1 = make_csv_row(content_id="post_001", title="First Post", views="1000")
        row2 = make_csv_row(content_id="post_002", title="Second Post", views="2000")
        row3 = make_csv_row(content_id="post_003", title="Third Post", views="3000")
        csv_data = make_csv_content([row1, row2, row3])

        records = load_content_csv(csv_data)
        self.assertEqual(len(records), 3)
        self.assertEqual([r.content_id for r in records], ["post_001", "post_002", "post_003"])
        self.assertEqual([r.views for r in records], [1000, 2000, 3000])

    def test_whitespace_handling(self):
        # Headers and text with whitespace
        spaced_headers = [f"  {col}  " for col in CSV_COLUMNS]
        header_line = ",".join(spaced_headers)
        row_str = make_csv_row(title="  Spaced Title  ", hook="  Interesting Hook  ")
        csv_data = f"{header_line}\n{row_str}\n\n"

        records = load_content_csv(io.StringIO(csv_data))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].title, "Spaced Title")
        self.assertEqual(records[0].hook, "Interesting Hook")

    def test_sample_dataset_loads_successfully(self):
        records = load_content_csv("data/sample/creator_history.csv")
        self.assertEqual(len(records), 40)
        for r in records:
            self.assertEqual(r.creator_id, "creator_ai_001")
            self.assertTrue(r.title)
            self.assertTrue(r.hook)
            self.assertGreaterEqual(r.views, 0)
            self.assertGreaterEqual(r.engagement_rate, 0.0)


if __name__ == "__main__":
    unittest.main()
