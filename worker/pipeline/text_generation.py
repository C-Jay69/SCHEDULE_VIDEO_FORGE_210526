import logging
import os
from typing import Any

from .providers.ollama import OllamaProvider
from .providers.openrouter import OpenRouterProvider

logger = logging.getLogger(__name__)

# Config
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
# Cloud fallback is OFF unless explicitly enabled. Default pipeline is 100% local (Ollama).
ENABLE_CLOUD_FALLBACK = os.getenv("ENABLE_CLOUD_FALLBACK", "false").lower() == "true"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")


class TextGenerationOrchestrator:
    """
    Orchestrates text generation by managing different providers.
    Implements fallback logic: Local (Ollama) -> Cloud (OpenRouter, opt-in only).
    """

    def __init__(self):
        self.providers = []

        # 1. Priority: Local Ollama
        self.providers.append(OllamaProvider(OLLAMA_BASE_URL, OLLAMA_MODEL))

        # 2. Fallback: OpenRouter (only if explicitly enabled AND API key exists)
        if ENABLE_CLOUD_FALLBACK and OPENROUTER_API_KEY:
            self.providers.append(OpenRouterProvider(OPENROUTER_API_KEY, OPENROUTER_MODEL))

        if not self.providers:
            logger.error("No text generation providers configured!")

    async def generate_script(self, topic: str, tone: str, style: str, duration_seconds: int) -> str:
        for provider in self.providers:
            try:
                logger.info(f"Attempting script generation with {provider.provider_name}...")
                return await provider.generate_script(topic, tone, style, duration_seconds)
            except Exception as e:
                logger.warning(f"Provider {provider.provider_name} failed: {e}")
                continue

        # Final absolute fallback
        return f"Fallback script for {topic}: This is a generated video about {topic}. Stay tuned for more!"

    async def generate_metadata(self, topic: str) -> dict[str, Any]:
        for provider in self.providers:
            try:
                logger.info(f"Attempting metadata generation with {provider.provider_name}...")
                return await provider.generate_metadata(topic)
            except Exception as e:
                logger.warning(f"Provider {provider.provider_name} failed: {e}")
                continue

        return {"title": topic[:70], "description": f"Video about {topic}", "tags": [topic]}


# Singleton for use across the worker
orchestrator = TextGenerationOrchestrator()

# --- Compatibility Layer for existing function calls ---


async def generate_script(
    topic: str, tone: str = "engaging", style: str = "informational", duration_seconds: int = 60
) -> str:
    return await orchestrator.generate_script(topic, tone, style, duration_seconds)


async def generate_title_and_tags(topic: str) -> dict:
    return await orchestrator.generate_metadata(topic)
