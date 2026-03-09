def test_invalid_request_exception(client):

    response = client.post(
        "/identify",
        json={}
    )

    assert response.status_code == 422

def test_database_connection_exception(monkeypatch, client):

    from app import database

    def mock_get_connection():
        raise Exception("Database unavailable")

    monkeypatch.setattr(database, "get_connection", mock_get_connection)

    response = client.post(
        "/identify",
        json={"email": "test@test.com"}
    )

    assert response.status_code >= 500