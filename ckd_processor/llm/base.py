"""
Base abstract class for LLM clients supporting text and vision/image payloads.
"""

from abc import ABC, abstractmethod
from typing import Optional, List


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "", images: Optional[List[str]] = None) -> str:
        """Generate text completion from LLM with optional base64 encoded images."""
        pass
