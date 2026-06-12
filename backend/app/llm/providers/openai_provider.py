"""OpenAI LLM provider — real implementation using OpenAI API."""

import json
import logging
import os

import httpx
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OpenAIProvider:
    provider_name = "openai"

    def __init__(self, api_key: str | None = None, model: str = "gpt-4.1-mini") -> None:
        settings = get_settings()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or getattr(settings, 'openai_api_key', None)
        self.model = model
        self.base_url = "https://api.openai.com/v1"
        self.timeout = 60.0

    def complete_json(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        """Call OpenAI API with structured output (JSON mode).

        Uses response_format={"type": "json_object"} for models that support it,
        falls back to parsing JSON from the response text.
        """
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured. Set it in .env or environment.")

        schema_json = json.dumps(schema.model_json_schema(), indent=2)

        system_prompt = (
            "You are a chemical sourcing procurement assistant. "
            "Respond ONLY with valid JSON that matches this exact schema:\n"
            f"{schema_json}\n\n"
            "Do not include any text outside the JSON object. "
            "Use null for missing/unknown values. Do not hallucinate."
        )

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4096,
                    "response_format": {"type": "json_object"},
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("OpenAI API error: %s", e)
            raise RuntimeError(f"OpenAI API request failed: {e}") from e

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        try:
            parsed = json.loads(content)
            return schema.model_validate(parsed)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Failed to parse OpenAI response as JSON: %s", e)
            logger.debug("Raw response: %s", content[:500])
            raise RuntimeError(f"OpenAI response could not be parsed as {schema.__name__}: {e}") from e
