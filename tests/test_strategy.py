import json
import os
import sys
import unittest
from unittest import mock

# Import the target function
from app.agent.strategy import generate_recommendation

# Import exception classes to mock behavior
from app.memory.hindsight_client import HindsightMemoryError


class TestStrategyAgent(unittest.TestCase):
    def setUp(self):
        # Ensure a clean environment for each test
        self.original_env = os.environ.copy()
        os.environ.pop('GROQ_API_KEY', None)
        os.environ.pop('HINDSIGHT_API_KEY', None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)
        # Remove any injected modules to avoid cross‑test contamination
        sys_modules = __import__('sys').modules
        sys_modules.pop('app.agent.strategy', None)
        sys_modules.pop('app.memory.hindsight_client', None)
        sys_modules.pop('app.llm.groq_client', None)

    def _mock_hindsight(self, memories):
        mock_client = mock.Mock()
        mock_client.recall_memories.return_value = memories
        return mock_client

    def test_successful_recommendation(self):
        # Mock memories returned from Hindsight
        memories = [{"text": "Created a tutorial on Python basics."}, {"text": "Published a video on data visualization."}]
        mock_hindsight = self._mock_hindsight(memories)
        # Mock Groq response JSON containing all required fields
        groq_response = {
            "recommendation": "Create an advanced data‑visualization series.",
            "why": "Both prior works focus on teaching fundamentals and visual storytelling.",
            "evidence": [memories[0]["text"], memories[1]["text"]],
            "content_gap": "Intermediate‑level tutorials are missing.",
            "suggested_experiment": "Release a short pilot episode and gauge engagement.",
            "learning_goal": "Teach complex chart types and interactivity.",
            "uncertainty": "Audience response to deeper topics is unknown."
        }
        # Patch get_hindsight_client and generate_strategy
        with mock.patch('app.agent.strategy.get_hindsight_client', return_value=mock_hindsight), \
             mock.patch('app.agent.strategy.generate_strategy', return_value=json.dumps(groq_response)):
            result = generate_recommendation('creator_ai_001')
            # Verify all required fields are present
            for field in ["recommendation", "why", "evidence", "content_gap", "suggested_experiment", "learning_goal", "uncertainty"]:
                self.assertIn(field, result)
            # Verify values match the mocked Groq response
            for field in ["recommendation", "why", "content_gap", "suggested_experiment", "learning_goal", "uncertainty"]:
                self.assertEqual(result[field], groq_response[field])
            # Verify evidence list contains the original memory texts
            self.assertEqual(result["evidence"], groq_response["evidence"])
            self.assertIn(memories[0]['text'], result['evidence'])
            self.assertIn(memories[1]['text'], result['evidence'])

    def test_hindsight_failure(self):
        # Simulate Hindsight client raising an error
        with mock.patch('app.agent.strategy.get_hindsight_client', side_effect=HindsightMemoryError('fail')):
            with self.assertRaises(RuntimeError) as ctx:
                generate_recommendation('creator_ai_001')
            self.assertIn('Failed to retrieve memories', str(ctx.exception))

    def test_groq_failure(self):
        mock_hindsight = self._mock_hindsight([{"text": "Sample memory."}])
        with mock.patch('app.agent.strategy.get_hindsight_client', return_value=mock_hindsight), \
             mock.patch('app.agent.strategy.generate_strategy', side_effect=RuntimeError('groq fail')):
            with self.assertRaises(RuntimeError) as ctx:
                generate_recommendation('creator_ai_001')
            self.assertIn('Failed to generate recommendation via Groq', str(ctx.exception))

    def test_invalid_json(self):
        mock_hindsight = self._mock_hindsight([{"text": "Memory."}])
        with mock.patch('app.agent.strategy.get_hindsight_client', return_value=mock_hindsight), \
             mock.patch('app.agent.strategy.generate_strategy', return_value='not a json'):
            with self.assertRaises(RuntimeError) as ctx:
                generate_recommendation('creator_ai_001')
            self.assertIn('Groq returned invalid JSON', str(ctx.exception))

    def test_missing_fields_in_output(self):
        mock_hindsight = self._mock_hindsight([{"text": "Memory."}])
        # JSON missing the 'why' field
        incomplete_response = {
            "recommendation": "Do X",
            "evidence": ["Memory."],
            "content_gap": "gap",
            "suggested_experiment": "exp",
            "learning_goal": "goal",
            "uncertainty": "uncert"
        }
        with mock.patch('app.agent.strategy.get_hindsight_client', return_value=mock_hindsight), \
             mock.patch('app.agent.strategy.generate_strategy', return_value=json.dumps(incomplete_response)):
            with self.assertRaises(RuntimeError) as ctx:
                generate_recommendation('creator_ai_001')
            self.assertIn('Groq output validation failed', str(ctx.exception))

if __name__ == '__main__':
    unittest.main()
