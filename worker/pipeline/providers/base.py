from abc import ABC, abstractmethod
from typing import Any


class TextGenerationProvider(ABC):
    """Base interface for all text generation providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the name of the provider (e.g., 'ollama', 'openrouter')."""
        pass

    @abstractmethod
    async def generate_script(self, topic: str, tone: str, style: str, duration_seconds: int) -> str:
        """Generates a raw video script."""
        pass

    @abstractmethod
    async def generate_metadata(self, topic: str) -> dict[str, Any]:
        """Generates title, description, and tags."""
        pass

    async def generate_scene_plan(
        self,
        topic: str,
        script: str,
        duration_seconds: int = 60,
    ) -> list[dict[str, Any]]:
        """Generates a shot-by-shot scene plan. Optional in the base interface.

        Returns a list of scenes, each with keys like:
        {'index': int, 'start': float, 'end': float, 'visual': str, 'on_screen_text': str}
        """
        # Default: divide the script evenly into 30s-max scenes with the topic as visual.
        raise NotImplementedError
