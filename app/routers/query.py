from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database import get_db
from app import models, schemas
from app.deps import get_current_user
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.generation_service import generate_answer
from app.services.groundedness_service import is_answer_grounded

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

@router.post("/query/ask", response_model=schemas.QueryResponseOut)
def ask_question(
    payload: schemas.QueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    chunks = retrieve_relevant_chunks(payload.question, current_user.company_id, db)

    if not chunks:
        return schemas.QueryResponseOut(
            answer="I don't have any documents to answer that yet — try uploading some first.",
            was_grounded=True,
            citations=[],
        )

    context_texts = [chunk.chunk_text for chunk in chunks]
    answer = generate_answer(payload.question, context_texts)
    grounded = is_answer_grounded(answer, context_texts)

    log_entry = models.QueryLog(
        company_id=current_user.company_id,
        question=payload.question,
        answer=answer,
        was_grounded=grounded,
        retrieved_chunk_ids=[c.id for c in chunks],
    )
    db.add(log_entry)
    db.commit()

    return schemas.QueryResponseOut(
        answer=answer,
        was_grounded=grounded,
        citations=[
            schemas.CitationOut(
                chunk_id=chunk.id,
                document_filename=chunk.document.filename,
                chunk_text=chunk.chunk_text,
            )
            for chunk in chunks
        ],
    )