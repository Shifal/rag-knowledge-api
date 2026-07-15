import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine, SessionLocal, ensure_pgvector_extension
from app import models


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    ensure_pgvector_extension()
    Base.metadata.create_all(bind=engine)
    yield
    db = SessionLocal()
    try:
        db.query(models.QueryLog).delete()
        db.query(models.DocumentChunk).delete()
        db.query(models.KnowledgeDocument).delete()
        db.query(models.User).delete()
        db.query(models.Company).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    response = client.post("/auth/signup", json={
        "company_name": "Test Company",
        "email": unique_email,
        "password": "TestPass123",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_gemini_calls():
    fake_embedding = [0.1] * 768

    with patch("app.services.embedding_service.embed_text", return_value=fake_embedding), \
         patch("app.services.embedding_service.embed_batch") as mock_embed_batch, \
         patch("app.graph.rag_graph.generate_answer") as mock_generate, \
         patch("app.graph.rag_graph.is_answer_grounded") as mock_grounded, \
         patch("app.graph.rag_graph._client") as mock_client:

        mock_embed_batch.side_effect = lambda texts: [fake_embedding for _ in texts]

        mock_generate.return_value = "This is a mocked answer based on the context."
        mock_grounded.return_value = True

        mock_response = type("MockResponse", (), {"text": "retrieve"})()
        mock_client.models.generate_content.return_value = mock_response

        yield {
            "embed_batch": mock_embed_batch,
            "generate": mock_generate,
            "grounded": mock_grounded,
            "client": mock_client,
        }


@pytest.fixture
def uploaded_document(client, auth_headers):
    test_content = b"Remote Work Policy\n\nEmployees may work remotely up to 3 days per week with manager approval."
    response = client.post(
        "/documents/upload",
        files={"file": ("test_policy.txt", test_content, "text/plain")},
        headers=auth_headers,
    )
    return response.json()