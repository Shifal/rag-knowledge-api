from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user
from app.services.ingestion_service import extract_text_from_upload

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

    document = models.KnowledgeDocument(
        company_id=current_user.company_id,
        filename=file.filename,
    )
    db.add(document)
    db.flush()

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