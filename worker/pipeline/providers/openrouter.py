import json
import logging
from typing import Any

import httpx

from .base import TextGenerationProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(TextGenerationProvider):
    def __init__(self, api_key: str, model: str = "meta-llama/llama-3.1-8b-instruct:free"):
        self.api_key = api_key
        self.model = model

    @property
    def provider_name(self) -> str:
        return "openrouter"

    async def generate_script(self, topic: str, tone: str, style: str, duration_seconds: int) -> str:
        prompt = f"""You are a professional short-form video script writer.
Write a {tone} video script about: {topic}
Requirements:
- Style: {style}
- Target duration: {duration_seconds} seconds
- Format for short-form vertical video
- Start with a strong hook
- Use conversational language
- End with a clear call to action
Return ONLY the script text, no stage directions or extra formatting."""

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "http://localhost:3000",
                        "X-Title": "VideoForge",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"OpenRouter script generation failed: {e}")
            raise

    async def generate_metadata(self, topic: str) -> dict[str, Any]:
        prompt = f"""You are a YouTube SEO expert. For a video about: {topic}
Generate: 1. title (max 70 chars), 2. description (2 sentences), 3. 10 tags (comma-separated).
Return ONLY a valid JSON object with keys: 'title', 'description', 'tags'."""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "http://localhost:3000",
                        "X-Title": "VideoForge",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                result = response.json()
                return json.loads(result["choices"][0]["message"]["content"])
        except Exception as e:
            logger.error(f"OpenRouter metadata generation failed: {e}")
            return {"title": topic[:70], "description": f"Video about {topic}", "tags": [topic]}
