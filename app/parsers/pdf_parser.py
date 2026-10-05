import fitz  # PyMuPDF
from .base import BaseParser, ParseResult, ParsedPage


class PDFParser(BaseParser):
    def parse(self, file_path: str) -> ParseResult:
        doc = fitz.open(file_path)
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                pages.append(ParsedPage(page_num=i + 1, text=text.strip()))
        doc.close()
        return ParseResult(pages=pages)
