from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user
from app.services.ingestion_service import extract_text_from_upload
from app.services.ingestion_service import extract_text_from_upload, chunk_text
from app.services.embedding_service import embed_batch

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=schemas.KnowledgeDocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    file_bytes = await file.read()

    try:
        extracted_text = extract_text_from_upload(file.filename, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in this file")

    chunks = chunk_text(extracted_text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Could not split document into chunks")

    embeddings = embed_batch(chunks)

    document = models.KnowledgeDocument(
        company_id=current_user.company_id,
        filename=file.filename,
    )
    db.add(document)
    db.flush()

    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_record = models.DocumentChunk(
            document_id=document.id,
            chunk_index=index,
            chunk_text=chunk,
            embedding=embedding,
        )
        db.add(chunk_record)

    db.commit()
    db.refresh(document)
    return document


@router.get("", response_model=List[schemas.KnowledgeDocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.KnowledgeDocument).filter(
        models.KnowledgeDocument.company_id == current_user.company_id
    ).all()

@router.get("/{document_id}/chunks", response_model=List[schemas.DocumentChunkOut])
def get_document_chunks(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    document = db.query(models.KnowledgeDocument).filter(
        models.KnowledgeDocument.id == document_id,
        models.KnowledgeDocument.company_id == current_user.company_id,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return db.query(models.DocumentChunk).filter(
        models.DocumentChunk.document_id == document_id
    ).order_by(models.DocumentChunk.chunk_index).all()