"""
Base abstract class for LLM clients.
"""

from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text completion from LLM."""
        pass
