from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session as DBSession
from ..db import get_db
from ..auth.dependencies import get_current_user
from ..db.models import User, UserRole
from ..dependencies import document_factory
from ..config import config
from pydantic import BaseModel
from pathlib import Path
import os

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


def _require_agent(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.AGENT,):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="agents only")
    return current_user


class DocumentInfo(BaseModel):
    filename: str
    size_bytes: int
    path: str


class IngestResponse(BaseModel):
    message: str
    chunks_uploaded: int
    filename: str


@router.get("/documents", response_model=list[DocumentInfo])
def list_documents(_: User = Depends(_require_agent)):
    """List all documents in the knowledge base directory."""
    kb_path = Path("knowledge-base")
    if not kb_path.exists():
        return []
    docs = []
    for f in kb_path.iterdir():
        if f.is_file() and f.suffix in (".md", ".txt", ".pdf"):
            docs.append(DocumentInfo(
                filename=f.name,
                size_bytes=f.stat().st_size,
                path=str(f)
            ))
    return docs


@router.post("/ingest", response_model=IngestResponse)
def ingest_document(
    filename: str = "faqs.md",
    _: User = Depends(_require_agent)
):
    """Re-ingest a document from the knowledge base into Pinecone."""
    filepath = Path("knowledge-base") / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found in knowledge base")

    text = document_factory.load_document(filepath=str(filepath))
    if not text:
        raise HTTPException(status_code=422, detail="Failed to load document content")

    chunks = document_factory.chunk_text(text=text)
    document_factory.upload_to_pinecone(chunks=chunks, namespace=config.PINECONE_NAMESPACE)

    return IngestResponse(
        message="Document ingested successfully.",
        chunks_uploaded=len(chunks),
        filename=filename
    )


@router.post("/upload", response_model=IngestResponse)
async def upload_and_ingest(
    file: UploadFile = File(...),
    _: User = Depends(_require_agent)
):
    """Upload a new .md or .txt document and ingest it immediately."""
    if not file.filename.endswith((".md", ".txt")):
        raise HTTPException(status_code=400, detail="Only .md and .txt files are supported")

    kb_path = Path("knowledge-base")
    kb_path.mkdir(exist_ok=True)
    dest = kb_path / file.filename

    content = await file.read()
    dest.write_bytes(content)

    text = content.decode("utf-8", errors="ignore").strip()
    if not text:
        raise HTTPException(status_code=422, detail="Uploaded file is empty")

    chunks = document_factory.chunk_text(text=text)
    document_factory.upload_to_pinecone(chunks=chunks, namespace=config.PINECONE_NAMESPACE)

    return IngestResponse(
        message="File uploaded and ingested successfully.",
        chunks_uploaded=len(chunks),
        filename=file.filename
    )
