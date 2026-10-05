from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParsedPage:
    page_num: int
    text: str


@dataclass
class ParseResult:
    pages: list[ParsedPage] = field(default_factory=list)

    @property
    def total_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> ParseResult:
        pass
