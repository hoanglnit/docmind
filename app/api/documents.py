import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.document import Document
from ..schemas.document import DocumentOut
from ..services import document_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    "text/csv",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload", response_model=DocumentOut, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File quá lớn (tối đa 50MB)")

    content_type = file.content_type or "text/plain"
    if content_type not in ALLOWED_TYPES:
        # Try to infer from extension
        ext = (file.filename or "").lower().rsplit(".", 1)[-1]
        ext_map = {"pdf": "application/pdf", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "txt": "text/plain", "md": "text/markdown", "csv": "text/csv"}
        content_type = ext_map.get(ext, "text/plain")

    file_path = document_service.save_upload(content, file.filename or "upload")

    doc = Document(
        name=file.filename or "Untitled",
        original_filename=file.filename or "upload",
        file_path=str(file_path),
        content_type=content_type,
        file_size=len(content),
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(document_service.process_document, doc.id, db)
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.created_at.desc()).all()


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    return doc


@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu")
    document_service.delete_document_files(doc)
    db.delete(doc)
    db.commit()
