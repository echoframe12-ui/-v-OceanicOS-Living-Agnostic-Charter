import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from claude_adapter import ClaudeAdapter, create_claude_adapter
from models import ModelAdapter, ModelRouter


def make_response(text="Hello from Claude", stop_reason="end_turn"):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        stop_reason=stop_reason,
        model="claude-opus-4-8",
    )


class ClaudeAdapterTests(unittest.TestCase):
    def test_factory_returns_none_without_api_key(self):
        with patch.dict("os.environ", {}, clear=False):
            import os

            os.environ.pop("ANTHROPIC_API_KEY", None)
            self.assertIsNone(create_claude_adapter())

    def test_generate_returns_text_output(self):
        client = MagicMock()
        client.messages.create.return_value = make_response()
        adapter = ClaudeAdapter(client=client)

        result = adapter.generate("Summarize the charter")

        self.assertEqual(result["output"], "Hello from Claude")
        self.assertEqual(result["provider"], "anthropic")
        call_kwargs = client.messages.create.call_args.kwargs
        self.assertEqual(call_kwargs["model"], "claude-opus-4-8")
        self.assertEqual(call_kwargs["thinking"], {"type": "adaptive"})

    def test_generate_reports_refusal_as_error(self):
        client = MagicMock()
        client.messages.create.return_value = make_response(stop_reason="refusal")
        adapter = ClaudeAdapter(client=client)

        result = adapter.generate("A declined request")

        self.assertEqual(result["error"], "refusal")
        self.assertNotIn("output", result)

    def test_describe_includes_model(self):
        client = MagicMock()
        adapter = ClaudeAdapter(client=client, keywords=["claude"])
        description = adapter.describe()
        self.assertEqual(description["model"], "claude-opus-4-8")
        self.assertEqual(description["keywords"], ["claude"])

    def test_router_routes_claude_prompts_to_adapter(self):
        client = MagicMock()
        client.messages.create.return_value = make_response()
        router = ModelRouter()
        router.register(ModelAdapter("local", "demo"))
        router.register(ClaudeAdapter(client=client, keywords=["claude"]))

        routed = router.route("Ask claude about the charter")
        self.assertEqual(routed["adapter"], "claude")

        fallback = router.route("hello")
        self.assertEqual(fallback["adapter"], "local")


if __name__ == "__main__":
    unittest.main()
