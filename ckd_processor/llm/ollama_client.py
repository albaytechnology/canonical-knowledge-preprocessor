"""
Ollama Client implementation supporting text and Vision/Multimodal payloads.
"""

import requests
from typing import Optional, List
from ckd_processor.llm.base import BaseLLMClient
from ckd_processor.utils.logger import setup_logger

logger = setup_logger("OllamaClient")


class OllamaLLMClient(BaseLLMClient):
    def __init__(
        self,
        model_name: str = "qwen3.6:35b",
        api_base: str = "http://172.16.10.142:11434",
        temperature: float = 0.0,
        timeout: int = 180,
        max_retries: int = 3
    ):
        self.model_name = model_name
        self.api_base = api_base.rstrip("/")
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

    def generate(self, prompt: str, system_prompt: str = "", images: Optional[List[str]] = None) -> str:
        url = f"{self.api_base}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        if images:
            payload["images"] = images

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "")
            except Exception as e:
                logger.warning(f"Ollama call attempt {attempt}/{self.max_retries} failed: {e}")
                if attempt == self.max_retries:
                    raise RuntimeError(f"Ollama API call failed after {self.max_retries} retries: {e}")
        return ""
