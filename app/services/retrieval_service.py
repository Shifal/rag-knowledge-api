from sqlalchemy.orm import Session
from sqlalchemy import select
from app import models
from app.services.embedding_service import embed_text


def retrieve_relevant_chunks(
    question: str,
    company_id: str,
    db: Session,
    top_k: int = 4,
) -> list[models.DocumentChunk]:

    question_embedding = embed_text(question)

    results = (
        db.query(models.DocumentChunk)
        .join(models.KnowledgeDocument)
        .filter(models.KnowledgeDocument.company_id == company_id)
        .order_by(models.DocumentChunk.embedding.cosine_distance(question_embedding))
        .limit(top_k)
        .all()
    )
    return results