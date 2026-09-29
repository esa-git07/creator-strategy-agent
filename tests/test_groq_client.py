import os
import sys
import unittest
from unittest import mock

# Ensure the groq_client module can be imported even if the real Groq SDK is absent.
# We'll inject a fake 'groq' module into sys.modules before importing.

# Create a minimal fake Groq SDK
class _FakeChatCompletions:
    def __init__(self, response):
        self._response = response

    def create(self, *args, **kwargs):
        return self._response

class _FakeGroq:
    def __init__(self, api_key):
        self.api_key = api_key
        self.chat = mock.Mock()
        # chat.completions will be a mock with create method set later
        self.chat.completions = mock.Mock()

# Helper to build a fake response object
def _build_fake_response(content):
    message = mock.Mock()
    message.content = content
    choice = mock.Mock()
    choice.message = message
    response = mock.Mock()
    response.choices = [choice]
    return response

class TestGroqClient(unittest.TestCase):
    def setUp(self):
        # Ensure environment is clean for each test
        self.original_env = os.environ.copy()
        if 'GROQ_API_KEY' in os.environ:
            del os.environ['GROQ_API_KEY']

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)
        # Remove injected modules to avoid cross‑test contamination
        sys.modules.pop('groq', None)

    def _import_with_fake_groq(self, fake_groq_instance):
        # Insert fake groq module
        fake_module = mock.Mock()
        fake_module.Groq = lambda api_key: fake_groq_instance
        sys.modules['groq'] = fake_module
        # Now import the client under test
        import importlib
        return importlib.import_module('app.llm.groq_client')

    def test_generate_strategy_success(self):
        os.environ['GROQ_API_KEY'] = 'test-key'
        fake_response = _build_fake_response('Generated strategy')
        fake_groq = _FakeGroq(api_key='test-key')
        fake_groq.chat.completions.create.return_value = fake_response
        client = self._import_with_fake_groq(fake_groq)
        result = client.generate_strategy('Explain strategy')
        self.assertEqual(result, 'Generated strategy')
        # Verify that the SDK was called with correct model
        fake_groq.chat.completions.create.assert_called_once()
        args, kwargs = fake_groq.chat.completions.create.call_args
        self.assertEqual(kwargs.get('model'), 'openai/gpt-oss-120b')
        self.assertIn('messages', kwargs)

    def test_missing_api_key(self):
        # Do not set GROQ_API_KEY
        client = self._import_with_fake_groq(_FakeGroq(api_key='should-not-be-used'))
        with self.assertRaises(RuntimeError) as ctx:
            client.generate_strategy('prompt')
        self.assertIn('GROQ API key not configured', str(ctx.exception))

    def test_api_error_propagates(self):
        os.environ['GROQ_API_KEY'] = 'test-key'
        fake_groq = _FakeGroq(api_key='test-key')
        fake_groq.chat.completions.create.side_effect = Exception('API failure')
        client = self._import_with_fake_groq(fake_groq)
        with self.assertRaises(RuntimeError) as ctx:
            client.generate_strategy('prompt')
        self.assertIn('Failed to generate strategy', str(ctx.exception))

    def test_empty_response(self):
        os.environ['GROQ_API_KEY'] = 'test-key'
        # Empty content
        fake_response = _build_fake_response('')
        fake_groq = _FakeGroq(api_key='test-key')
        fake_groq.chat.completions.create.return_value = fake_response
        client = self._import_with_fake_groq(fake_groq)
        with self.assertRaises(RuntimeError) as ctx:
            client.generate_strategy('prompt')
        self.assertIn('Empty response', str(ctx.exception))

if __name__ == '__main__':
    unittest.main()
