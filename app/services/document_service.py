import logging
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..models.document import Document
from ..config import settings
from ..parsers import get_parser
from . import embedding_service
from .. import vector_store

logger = logging.getLogger(__name__)

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
)


def save_upload(content: bytes, filename: str) -> Path:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix or ".bin"
    dest = settings.upload_dir / f"{uuid.uuid4()}{suffix}"
    dest.write_bytes(content)
    return dest


def process_document(document_id: str, db: Session):
    doc = db.get(Document, document_id)
    if not doc:
        return

    try:
        parser = get_parser(doc.content_type)
        result = parser.parse(doc.file_path)

        if not result.pages:
            raise ValueError("Không trích xuất được nội dung từ tài liệu")

        chunks_with_meta = []  # type: ignore
        for page in result.pages:
            for chunk_text in _splitter.split_text(page.text):
                chunks_with_meta.append({
                    "text": chunk_text,
                    "metadata": {
                        "document_id": document_id,
                        "source": doc.original_filename,
                        "page": page.page_num,
                    },
                })

        if not chunks_with_meta:
            raise ValueError("Không tạo được chunks từ tài liệu")

        texts = [c["text"] for c in chunks_with_meta]
        embeddings = embedding_service.embed_texts(texts)

        vector_store.add_chunks(
            document_id=document_id,
            chunks=texts,
            embeddings=embeddings,
            metadatas=[c["metadata"] for c in chunks_with_meta],
        )

        doc.chunk_count = len(chunks_with_meta)
        doc.status = "ready"
        db.commit()
        logger.info("Document %s processed: %d chunks", document_id, len(chunks_with_meta))

    except Exception as e:
        logger.exception("Failed to process document %s", document_id)
        doc.status = "error"
        doc.error_message = str(e)
        db.commit()


def delete_document_files(doc: Document):
    vector_store.delete_document(doc.id)
    path = Path(doc.file_path)
    if path.exists():
        path.unlink(missing_ok=True)
