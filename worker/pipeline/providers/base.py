from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class TextGenerationProvider(ABC):
    """Base interface for all text generation providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the name of the provider (e.g., 'ollama', 'openrouter')."""
        pass

    @abstractmethod
    async def generate_script(
        self, 
        topic: str, 
        tone: str, 
        style: str, 
        duration_seconds: int
    ) -> str:
        """Generates a raw video script."""
        pass

    @abstractmethod
    async def generate_metadata(self, topic: str) -> Dict[str, Any]:
        """Generates title, description, and tags."""
        pass
