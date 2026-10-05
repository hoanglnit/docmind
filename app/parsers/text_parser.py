from .base import BaseParser, ParseResult, ParsedPage


class TextParser(BaseParser):
    def parse(self, file_path: str) -> ParseResult:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()
        pages = [ParsedPage(page_num=1, text=text)] if text else []
        return ParseResult(pages=pages)
