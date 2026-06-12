"""Anthropic Claude LLM provider — real implementation using Anthropic API."""

import json
import logging
import os

import httpx
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class AnthropicProvider:
    provider_name = "anthropic"

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-6") -> None:
        settings = get_settings()
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or getattr(settings, 'anthropic_api_key', None)
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"
        self.timeout = 60.0
        self.anthropic_version = "2023-06-01"

    def complete_json(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        """Call Anthropic Claude API with structured JSON output.

        Uses tool use / extended thinking to ensure valid JSON responses
        that match the given Pydantic schema.
        """
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured. Set it in .env or environment.")

        schema_json = json.dumps(schema.model_json_schema(), indent=2)

        system_prompt = (
            "You are a chemical sourcing procurement assistant. "
            "You MUST respond with ONLY a valid JSON object that matches this exact schema. "
            "Do NOT include any text, markdown, or explanation outside the JSON.\n\n"
            "Schema:\n"
            f"{schema_json}\n\n"
            "Rules:\n"
            "- Use null for missing or unknown values — do not hallucinate\n"
            "- Do not guess CAS numbers, prices, certificates, or regulatory statuses\n"
            "- All output must be parseable by Python's json.loads()"
        )

        try:
            response = httpx.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": self.anthropic_version,
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 4096,
                    "system": system_prompt,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("Anthropic API error: %s", e)
            raise RuntimeError(f"Anthropic API request failed: {e}") from e

        data = response.json()
        content = data["content"][0]["text"]

        # Strip markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:]) if len(lines) > 1 else content
        if content.endswith("```"):
            content = content[:-3].strip()

        try:
            parsed = json.loads(content)
            return schema.model_validate(parsed)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Failed to parse Claude response as JSON: %s", e)
            logger.debug("Raw response: %s", content[:500])
            raise RuntimeError(f"Claude response could not be parsed as {schema.__name__}: {e}") from e
