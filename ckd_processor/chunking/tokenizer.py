"""
Tokenizer abstraction for token counting.
"""

from abc import ABC, abstractmethod


class BaseTokenizer(ABC):
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        pass


class SimpleWordTokenizer(BaseTokenizer):
    """Fallback tokenizer estimating tokens (~1.3 tokens per word)."""
    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        words = text.split()
        return max(1, int(len(words) * 1.3))


class TiktokenTokenizer(BaseTokenizer):
    """Tiktoken-based accurate token counter if available."""
    def __init__(self, model_name: str = "gpt-4o"):
        try:
            import tiktoken
            self.encoding = tiktoken.encoding_for_model(model_name)
        except Exception:
            try:
                import tiktoken
                self.encoding = tiktoken.get_encoding("cl100k_base")
            except Exception:
                self.encoding = None

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        if self.encoding:
            return len(self.encoding.encode(text))
        # Fallback if tiktoken fails
        return int(len(text.split()) * 1.3)


def get_tokenizer(tokenizer_type: str = "word") -> BaseTokenizer:
    if tokenizer_type == "tiktoken":
        try:
            return TiktokenTokenizer()
        except Exception:
            return SimpleWordTokenizer()
    return SimpleWordTokenizer()
