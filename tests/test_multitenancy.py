import uuid


def test_company_cannot_see_another_companys_documents(client):
    email_a = f"companya_{uuid.uuid4().hex[:8]}@example.com"
    signup_a = client.post("/auth/signup", json={
        "company_name": "Company A", "email": email_a, "password": "PassA123",
    })
    headers_a = {"Authorization": f"Bearer {signup_a.json()['access_token']}"}

    client.post(
        "/documents/upload",
        files={"file": ("secret.txt", b"Company A confidential info", "text/plain")},
        headers=headers_a,
    )

    email_b = f"companyb_{uuid.uuid4().hex[:8]}@example.com"
    signup_b = client.post("/auth/signup", json={
        "company_name": "Company B", "email": email_b, "password": "PassB123",
    })
    headers_b = {"Authorization": f"Bearer {signup_b.json()['access_token']}"}

    response_b = client.get("/documents", headers=headers_b)
    assert response_b.status_code == 200
    assert response_b.json() == []


def test_unauthenticated_request_is_rejected(client):
    response = client.get("/documents")
    assert response.status_code == 401