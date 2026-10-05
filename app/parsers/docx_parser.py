from docx import Document as DocxDocument
from .base import BaseParser, ParseResult, ParsedPage


class DocxParser(BaseParser):
    def parse(self, file_path: str) -> ParseResult:
        doc = DocxDocument(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        pages = [ParsedPage(page_num=1, text=text)] if text else []
        return ParseResult(pages=pages)
