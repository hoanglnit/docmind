from .pdf_parser import PDFParser
from .docx_parser import DocxParser
from .text_parser import TextParser

PARSER_MAP = {
    "application/pdf": PDFParser(),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxParser(),
    "text/plain": TextParser(),
    "text/markdown": TextParser(),
    "text/csv": TextParser(),
}


def get_parser(content_type: str):
    return PARSER_MAP.get(content_type, TextParser())
