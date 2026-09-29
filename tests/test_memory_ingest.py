# """
# Unit tests for the memory ingestion layer.
# """

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the ingestion function and helper types
from app.memory.ingest import ingest_creator_history
from app.data.schema import ContentRecord

class TestMemoryIngest(unittest.TestCase):
    def setUp(self):
        # Sample ContentRecord objects for testing
        self.sample_records = [
            ContentRecord(
                content_id="c1",
                creator_id="creator_ai_001",
                date=__import__("datetime").date(2023, 1, 1),
                platform="YouTube",
                title="Intro to AI",
                topic="Artificial Intelligence",
                format="Video",
                hook="Learn AI",
                views=1000,
                likes=100,
                comments=10,
                shares=5,
                saves=2,
                engagement_rate=10.5,
                audience_feedback="Positive",
                creator_notes="First video",
            ),
            ContentRecord(
                content_id="c2",
                creator_id="creator_ai_001",
                date=__import__("datetime").date(2023, 2, 1),
                platform="Twitter",
                title="AI Thread",
                topic="Machine Learning",
                format="Thread",
                hook="Deep dive",
                views=2000,
                likes=150,
                comments=20,
                shares=10,
                saves=5,
                engagement_rate=12.0,
                audience_feedback="Mixed",
                creator_notes="Thread series",
            ),
        ]

    @patch("app.memory.ingest.load_content_csv")
    @patch("app.memory.ingest.get_hindsight_client")
    def test_ingest_successful(self, mock_client_factory, mock_loader):
        # Mock loader to return our sample records
        mock_loader.return_value = self.sample_records

        # Mock Hindsight client with retain and recall methods
        mock_client = MagicMock()
        # recall returns empty list (no duplicates)
        mock_client.recall_memories.return_value = []
        # retain returns a dummy success dict
        mock_client.retain_memory.return_value = {
            "success": True,
            "bank_id": "creator_ai_001",
            "items_count": 1,
            "operation_id": "op-123",
        }
        mock_client_factory.return_value = mock_client

        summary = ingest_creator_history(csv_path=Path("dummy.csv"))

        # Ensure loader called with the dummy path
        mock_loader.assert_called_once()
        # Ensure recall was called for each record
        self.assertEqual(mock_client.recall_memories.call_count, len(self.sample_records))
        # Ensure retain was called for each record
        self.assertEqual(mock_client.retain_memory.call_count, len(self.sample_records))
        # Verify summary contains retained entries for both records
        self.assertEqual(len(summary["retained"]), 2)
        self.assertEqual(summary["skipped"], [])
        self.assertEqual(summary["failed"], [])

    @patch("app.memory.ingest.load_content_csv")
    @patch("app.memory.ingest.get_hindsight_client")
    def test_duplicate_skipping(self, mock_client_factory, mock_loader):
        mock_loader.return_value = self.sample_records
        mock_client = MagicMock()
        # First record appears as duplicate, second is new
        mock_client.recall_memories.side_effect = [
            [{"text": "... c1 ...", "metadata": {"content_id": "c1"}}],
            [],
        ]
        mock_client.retain_memory.return_value = {
            "success": True,
            "bank_id": "creator_ai_001",
            "items_count": 1,
            "operation_id": "op-456",
        }
        mock_client_factory.return_value = mock_client

        summary = ingest_creator_history(csv_path=Path("dummy.csv"))
        # First record skipped, second retained
        self.assertEqual(len(summary["skipped"]), 1)
        self.assertEqual(summary["skipped"][0]["content_id"], "c1")
        self.assertEqual(len(summary["retained"]), 1)
        self.assertEqual(summary["retained"][0]["content_id"], "c2")

    @patch("app.memory.ingest.load_content_csv")
    @patch("app.memory.ingest.get_hindsight_client")
    def test_retain_error_handling(self, mock_client_factory, mock_loader):
        mock_loader.return_value = self.sample_records
        mock_client = MagicMock()
        mock_client.recall_memories.return_value = []
        # Simulate HindsightMemoryError on retain for first record
        from app.memory.hindsight_client import HindsightMemoryError
        mock_client.retain_memory.side_effect = [HindsightMemoryError("boom"), {
            "success": True,
            "bank_id": "creator_ai_001",
            "items_count": 1,
            "operation_id": "op-789",
        }]
        mock_client_factory.return_value = mock_client

        summary = ingest_creator_history(csv_path=Path("dummy.csv"))
        self.assertEqual(len(summary["failed"]), 1)
        self.assertEqual(summary["failed"][0]["content_id"], "c1")
        self.assertIn("boom", summary["failed"][0]["error"])
        self.assertEqual(len(summary["retained"]), 1)
        self.assertEqual(summary["retained"][0]["content_id"], "c2")

if __name__ == "__main__":
    unittest.main()
