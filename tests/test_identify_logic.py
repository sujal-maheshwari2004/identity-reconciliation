def test_create_new_primary(client):
    """
    Case 1:
    No existing contact → create primary
    """

    response = client.post(
        "/identify",
        json={"email": "doc@hillvalley.edu"}
    )

    assert response.status_code == 200

    data = response.json()["contact"]

    assert data["emails"] == ["doc@hillvalley.edu"]
    assert data["secondaryContactIds"] == []

def test_exact_match_returns_cluster(client):
    """
    Case 2:
    Exact same contact → no new records
    """

    client.post(
        "/identify",
        json={
            "email": "lorraine@hillvalley.edu",
            "phoneNumber": "123456"
        }
    )

    response = client.post(
        "/identify",
        json={
            "email": "lorraine@hillvalley.edu",
            "phoneNumber": "123456"
        }
    )

    data = response.json()["contact"]

    assert data["emails"] == ["lorraine@hillvalley.edu"]
    assert data["phoneNumbers"] == ["123456"]

def test_create_secondary_contact(client):
    """
    Case 3:
    Partial match with new information → create secondary
    """

    client.post(
        "/identify",
        json={
            "email": "lorraine@hillvalley.edu",
            "phoneNumber": "123456"
        }
    )

    response = client.post(
        "/identify",
        json={
            "email": "mcfly@hillvalley.edu",
            "phoneNumber": "123456"
        }
    )

    data = response.json()["contact"]

    assert "lorraine@hillvalley.edu" in data["emails"]
    assert "mcfly@hillvalley.edu" in data["emails"]

    assert data["phoneNumbers"] == ["123456"]
    assert len(data["secondaryContactIds"]) == 1

def test_merge_two_clusters(client):
    """
    Case 4:
    Two primary clusters become linked → one must demote
    """

    client.post(
        "/identify",
        json={
            "email": "george@hillvalley.edu",
            "phoneNumber": "919191"
        }
    )

    client.post(
        "/identify",
        json={
            "email": "biffsucks@hillvalley.edu",
            "phoneNumber": "717171"
        }
    )

    response = client.post(
        "/identify",
        json={
            "email": "george@hillvalley.edu",
            "phoneNumber": "717171"
        }
    )

    data = response.json()["contact"]

    assert len(data["emails"]) == 2
    assert len(data["phoneNumbers"]) == 2
    assert len(data["secondaryContactIds"]) >= 1