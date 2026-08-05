import json
import logging
from typing import Any

import httpx

from .base import TextGenerationProvider

logger = logging.getLogger(__name__)


class OllamaProvider(TextGenerationProvider):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def generate_script(self, topic: str, tone: str, style: str, duration_seconds: int) -> str:
        prompt = f"""You are a professional short-form video script writer.
Write a {tone} video script about: {topic}
Requirements:
- Style: {style}
- Target duration: {duration_seconds} seconds
- Format for short-form vertical video (TikTok/YouTube Shorts/Instagram Reels)
- Start with a strong hook
- Use conversational language
- End with a clear call to action
Return ONLY the script text, no stage directions or extra formatting."""

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": 0.8}},
                )
                response.raise_for_status()
                return response.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama script generation failed: {e}")
            raise

    async def generate_metadata(self, topic: str) -> dict[str, Any]:
        prompt = f"""You are a YouTube SEO expert. For a video about: {topic}
Generate: 1. title (max 70 chars), 2. description (2 sentences), 3. 10 tags (comma-separated).
Return ONLY a valid JSON object with keys: 'title', 'description', 'tags'."""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
                )
                response.raise_for_status()
                data = response.json()
                return json.loads(data.get("response", "{}"))
        except Exception as e:
            logger.error(f"Ollama metadata generation failed: {e}")
            return {"title": topic[:70], "description": f"Video about {topic}", "tags": [topic]}

    async def generate_scene_plan(self, topic: str, script: str, duration_seconds: int = 60) -> list:
        prompt = f"""You are a video director. For a short-form video about: {topic}

Script:
{script[:1500]}

Break the script into a shot-by-shot scene plan covering {duration_seconds} seconds.
Return ONLY a valid JSON array. Each scene object has keys: 'visual' (what is shown on screen),
'on_screen_text' (burned-in caption text), 'start' (float seconds), 'end' (float seconds)."""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
                )
                response.raise_for_status()
                data = response.json()
                return json.loads(data.get("response", "[]"))
        except Exception as e:
            logger.error(f"Ollama scene plan generation failed: {e}")
            raise

    async def generate_cta(self, topic: str) -> str:
        prompt = f"""You are a short-form video marketer. Write ONE punchy call-to-action
line (max 8 words) to close a video about: {topic}. Return ONLY the CTA text."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate", json={"model": self.model, "prompt": prompt, "stream": False}
                )
                response.raise_for_status()
                return response.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama CTA generation failed: {e}")
            raise
