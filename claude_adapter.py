from __future__ import annotations

import os
from typing import Any

from models import ModelAdapter


class ClaudeAdapter(ModelAdapter):
    """Route prompts to a real Claude model through the official Anthropic SDK.

    The adapter degrades gracefully: construction requires the anthropic
    package (and, for the default client, ANTHROPIC_API_KEY), and API errors
    are returned as structured results instead of raised, so a failed model
    call never breaks the builder pipeline.
    """

    def __init__(
        self,
        name: str = "claude",
        model: str = "claude-opus-4-8",
        keywords: list[str] | None = None,
        client: Any | None = None,
    ) -> None:
        super().__init__(name, "anthropic", keywords)
        self.model = model
        if client is None:
            import anthropic

            client = anthropic.Anthropic()
        self._client = client

    def generate(self, prompt: str) -> dict[str, Any]:
        import anthropic

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=16000,
                thinking={"type": "adaptive"},
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.RateLimitError:
            return self._error(prompt, "rate_limited")
        except anthropic.APIStatusError as error:
            return self._error(prompt, f"api_error_{error.status_code}")
        except anthropic.APIConnectionError:
            return self._error(prompt, "connection_error")

        if response.stop_reason == "refusal":
            return self._error(prompt, "refusal")

        output = "".join(
            block.text for block in response.content if block.type == "text"
        )
        return {
            "adapter": self.name,
            "provider": self.provider,
            "prompt": prompt,
            "model": response.model,
            "output": output,
        }

    def describe(self) -> dict[str, Any]:
        description = super().describe()
        description["model"] = self.model
        return description

    def _error(self, prompt: str, code: str) -> dict[str, Any]:
        return {
            "adapter": self.name,
            "provider": self.provider,
            "prompt": prompt,
            "error": code,
        }


def create_claude_adapter(keywords: list[str] | None = None) -> ClaudeAdapter | None:
    """Build a ClaudeAdapter when credentials and the SDK are available."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return None
    return ClaudeAdapter(keywords=keywords or ["claude"])
