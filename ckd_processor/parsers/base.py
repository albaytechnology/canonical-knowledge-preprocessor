"""
Base Abstract Parser and Parser Registry architecture.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PageContent(BaseModel):
    page_number: int
    text: str
    has_images: bool = False
    is_ocr: bool = False


class ParsedDocument(BaseModel):
    filepath: str
    filename: str
    extension: str
    pages: List[PageContent]
    full_raw_text: str
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseParser(ABC):
    """Abstract Base Class for all document parsers."""

    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Return list of supported file extensions (lowercase without dot)."""
        pass

    @abstractmethod
    def parse(self, filepath: str) -> ParsedDocument:
        """Parse file and return structured ParsedDocument."""
        pass


class ParserRegistry:
    """Registry to register and resolve document parsers dynamically."""

    def __init__(self):
        self._parsers: Dict[str, BaseParser] = {}

    def register(self, parser: BaseParser) -> None:
        for ext in parser.supported_extensions():
            self._parsers[ext.lower()] = parser

    def get_parser(self, filepath: str) -> Optional[BaseParser]:
        ext = filepath.split(".")[-1].lower() if "." in filepath else ""
        return self._parsers.get(ext)

    def supports(self, filepath: str) -> bool:
        ext = filepath.split(".")[-1].lower() if "." in filepath else ""
        return ext in self._parsers
