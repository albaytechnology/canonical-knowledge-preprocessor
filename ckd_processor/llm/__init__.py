"""
LLM Factory and package exports.
"""

from ckd_processor.llm.base import BaseLLMClient
from ckd_processor.llm.ollama_client import OllamaLLMClient
from ckd_processor.llm.openai_client import OpenAILLMClient
from ckd_processor.llm.mock_client import MockLLMClient
from ckd_processor.config import LLMConfig


def get_llm_client(config: LLMConfig) -> BaseLLMClient:
    provider = config.provider.lower()
    if provider == "ollama":
        return OllamaLLMClient(
            model_name=config.model_name,
            api_base=config.api_base,
            temperature=config.temperature,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
    elif provider == "openai":
        return OpenAILLMClient(
            model_name=config.model_name,
            api_base=config.api_base,
            api_key=config.api_key,
            temperature=config.temperature,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
    else:
        return MockLLMClient()
