from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database import get_db
from app import models
from app.deps import get_current_user
from app.services.retrieval_service import retrieve_relevant_chunks

router = APIRouter(tags=["query"])


class RetrievalTestRequest(BaseModel):
    question: str


class RetrievedChunkOut(BaseModel):
    chunk_id: str
    chunk_text: str
    document_filename: str

    class Config:
        from_attributes = True


@router.post("/query/test-retrieval", response_model=List[RetrievedChunkOut])
def test_retrieval(
    payload: RetrievalTestRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    chunks = retrieve_relevant_chunks(payload.question, current_user.company_id, db)
    return [
        RetrievedChunkOut(
            chunk_id=chunk.id,
            chunk_text=chunk.chunk_text,
            document_filename=chunk.document.filename,
        )
        for chunk in chunks
    ]