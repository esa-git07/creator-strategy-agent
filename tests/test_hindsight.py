import os
import unittest
from unittest.mock import MagicMock, patch

from dotenv import load_dotenv

load_dotenv()

from app.memory.hindsight_client import (
    HindsightConfigurationError,
    HindsightConnectionError,
    HindsightMemoryClient,
    HindsightMemoryError,
    get_hindsight_client,
)


class TestHindsightUnit(unittest.TestCase):
    """
    Unit tests that execute entirely offline without requiring live Hindsight credentials.
    """

    def test_missing_api_key_raises_configuration_error(self):
        with patch.dict(os.environ, {"HINDSIGHT_API_KEY": ""}, clear=False):
            # Explicitly pass empty API key and cloud URL
            with self.assertRaises(HindsightConfigurationError) as ctx:
                HindsightMemoryClient(
                    api_key="",
                    base_url="https://api.hindsight.vectorize.io",
                )
            self.assertIn("HINDSIGHT_API_KEY is not configured", str(ctx.exception))

    def test_repr_does_not_expose_api_key(self):
        secret_key = "sk_secret_123456789"
        client = HindsightMemoryClient(
            api_key=secret_key,
            base_url="http://localhost:8888",
        )
        rep = repr(client)
        self.assertNotIn(secret_key, rep)
        self.assertIn("[SET]", rep)

    def test_sanitize_message_masks_api_key(self):
        secret_key = "sk_very_secret_hindsight_token"
        client = HindsightMemoryClient(
            api_key=secret_key,
            base_url="http://localhost:8888",
        )
        dirty_error = f"Unauthorized error connecting with key: {secret_key}"
        cleaned = client._sanitize_message(dirty_error)
        self.assertNotIn(secret_key, cleaned)
        self.assertIn("[REDACTED]", cleaned)

    def test_empty_arguments_validation(self):
        client = HindsightMemoryClient(
            api_key="test_key",
            base_url="http://localhost:8888",
        )
        with self.assertRaises(ValueError):
            client.retain_memory(bank_id="", content="Some content")

        with self.assertRaises(ValueError):
            client.retain_memory(bank_id="bank1", content="   ")

        with self.assertRaises(ValueError):
            client.recall_memories(bank_id="", query="Some query")

        with self.assertRaises(ValueError):
            client.recall_memories(bank_id="bank1", query="   ")

    def test_retain_memory_unit_with_mock(self):
        client = HindsightMemoryClient(
            api_key="test_key",
            base_url="http://localhost:8888",
        )
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.bank_id = "test_creator_ai_001"
        mock_response.items_count = 1
        mock_response.operation_id = "op_123"

        client._client.retain = MagicMock(return_value=mock_response)

        res = client.retain_memory(
            bank_id="test_creator_ai_001",
            content="Test memory: actionable AI tutorials produced strong save behavior.",
            context="Creator post-mortem",
            metadata={"source": "test"},
        )

        client._client.retain.assert_called_once_with(
            bank_id="test_creator_ai_001",
            content="Test memory: actionable AI tutorials produced strong save behavior.",
            context="Creator post-mortem",
            metadata={"source": "test"},
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["bank_id"], "test_creator_ai_001")
        self.assertEqual(res["items_count"], 1)

    def test_recall_memories_unit_with_mock(self):
        client = HindsightMemoryClient(
            api_key="test_key",
            base_url="http://localhost:8888",
        )
        mock_item = MagicMock()
        mock_item.id = "mem_001"
        mock_item.text = "Test memory: actionable AI tutorials produced strong save behavior."
        mock_item.type = "observation"
        mock_item.context = "Creator post-mortem"
        mock_item.metadata = {"source": "test"}
        mock_item.scores = {"relevance": 0.95}

        mock_response = MagicMock()
        mock_response.results = [mock_item]

        client._client.recall = MagicMock(return_value=mock_response)

        results = client.recall_memories(
            bank_id="test_creator_ai_001",
            query="actionable AI tutorials save behavior",
        )

        client._client.recall.assert_called_once_with(
            bank_id="test_creator_ai_001",
            query="actionable AI tutorials save behavior",
            max_tokens=4096,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "mem_001")
        self.assertIn("actionable AI tutorials", results[0]["text"])

    def test_error_wrapping_on_client_failure(self):
        client = HindsightMemoryClient(
            api_key="test_key",
            base_url="http://localhost:8888",
        )
        client._client.retain = MagicMock(side_effect=RuntimeError("Connection refused by peer"))

        with self.assertRaises(HindsightMemoryError) as ctx:
            client.retain_memory(
                bank_id="test_bank",
                content="test content",
            )
        self.assertIn("Failed to retain memory in Hindsight", str(ctx.exception))


class TestHindsightLiveIntegration(unittest.TestCase):
    """
    Live integration test against the real Hindsight service.
    This test only runs if HINDSIGHT_API_KEY is configured in the environment.
    """

    @unittest.skipUnless(
        os.getenv("HINDSIGHT_API_KEY"),
        "HINDSIGHT_API_KEY not configured, skipping live integration test",
    )
    def test_live_write_and_read(self):
        client = get_hindsight_client()
        test_bank = "test_creator_ai_001"
        test_experience = "Test memory: actionable AI tutorials produced strong save behavior."

        # Write (Retain)
        retain_res = client.retain_memory(
            bank_id=test_bank,
            content=test_experience,
            metadata={"test_run": "true"},
        )
        self.assertTrue(retain_res.get("success", False))

        # Read (Recall)
        recall_res = client.recall_memories(
            bank_id=test_bank,
            query="What format produced strong save behavior?",
        )
        self.assertIsInstance(recall_res, list)


if __name__ == "__main__":
    unittest.main()
