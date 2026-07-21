"""
OpenAI / OpenAI-compatible vLLM / LiteLLM API client.
"""

import requests
from typing import Optional
from ckd_processor.llm.base import BaseLLMClient
from ckd_processor.utils.logger import setup_logger

logger = setup_logger("OpenAIClient")


class OpenAILLMClient(BaseLLMClient):
    def __init__(
        self,
        model_name: str = "gpt-4o",
        api_base: str = "https://api.openai.com/v1",
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        timeout: int = 120,
        max_retries: int = 3
    ):
        self.model_name = model_name
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries

    def generate(self, prompt: str, system_prompt: str = "", images: Optional[List[str]] = None) -> str:
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.warning(f"OpenAI call attempt {attempt}/{self.max_retries} failed: {e}")
                if attempt == self.max_retries:
                    raise RuntimeError(f"OpenAI API call failed after {self.max_retries} retries: {e}")
        return ""
