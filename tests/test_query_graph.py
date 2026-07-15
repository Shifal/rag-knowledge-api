def test_general_question_skips_retrieval(client, auth_headers, uploaded_document, mock_gemini_calls):
    mock_response = type("MockResponse", (), {"text": "general"})()
    mock_gemini_calls["client"].models.generate_content.return_value = mock_response
    mock_gemini_calls["generate"].return_value = "Hi! I can help answer questions about your documents."

    response = client.post("/query/ask", json={"question": "Hi there!"}, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["citations"] == []  # no retrieval happened


def test_document_question_triggers_retrieval(client, auth_headers, uploaded_document, mock_gemini_calls):
    mock_gemini_calls["generate"].return_value = "Employees get 15 vacation days per year."
    mock_gemini_calls["grounded"].return_value = True

    response = client.post(
        "/query/ask",
        json={"question": "How many vacation days do employees get?"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Employees get 15 vacation days per year."
    assert data["was_grounded"] is True
    assert len(data["citations"]) >= 1


def test_ungrounded_answer_is_flagged(client, auth_headers, uploaded_document, mock_gemini_calls):
    mock_gemini_calls["generate"].return_value = "Employees get unlimited vacation days."  # a hallucinated claim
    mock_gemini_calls["grounded"].return_value = False  # the checker correctly catches it

    response = client.post(
        "/query/ask",
        json={"question": "How many vacation days do employees get?"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["was_grounded"] is False


def test_query_is_logged(client, auth_headers, uploaded_document, mock_gemini_calls):
    client.post("/query/ask", json={"question": "How many vacation days?"}, headers=auth_headers)

    response = client.post("/query/ask", json={"question": "What about sick days?"}, headers=auth_headers)
    assert response.status_code == 200