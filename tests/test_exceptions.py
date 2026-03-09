def test_invalid_request_exception(client):

    response = client.post(
        "/identify",
        json={}
    )

    assert response.status_code == 422