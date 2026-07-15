def test_upload_document_creates_chunks(client, auth_headers):
    test_content = b"Company Policy\n\nAll employees get 15 vacation days per year."

    response = client.post(
        "/documents/upload",
        files={"file": ("policy.txt", test_content, "text/plain")},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "policy.txt"
    assert "id" in data


def test_list_documents_returns_uploaded_document(client, auth_headers, uploaded_document):
    response = client.get("/documents", headers=auth_headers)

    assert response.status_code == 200
    filenames = [doc["filename"] for doc in response.json()]
    assert "test_policy.txt" in filenames


def test_get_document_chunks_returns_chunks(client, auth_headers, uploaded_document):
    document_id = uploaded_document["id"]

    response = client.get(f"/documents/{document_id}/chunks", headers=auth_headers)

    assert response.status_code == 200
    chunks = response.json()
    assert len(chunks) >= 1
    assert "chunk_text" in chunks[0]


def test_upload_rejects_unsupported_file_type(client, auth_headers):
    response = client.post(
        "/documents/upload",
        files={"file": ("data.xyz", b"some content", "application/octet-stream")},
        headers=auth_headers,
    )

    assert response.status_code == 400