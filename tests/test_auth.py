REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/users/me"

USER = {"email": "khaled@example.com", "full_name": "Khaled", "password": "12345678"}


def register(client, **overrides):
    return client.post(REGISTER_URL, json={**USER, **overrides})


def login(client, email=USER["email"], password=USER["password"]):
    return client.post(LOGIN_URL, data={"username": email, "password": password})


def test_register_success(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == USER["email"]
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email(client):
    register(client)
    assert register(client).status_code == 409


def test_register_email_is_case_insensitive(client):
    register(client)
    assert register(client, email="KHALED@example.com").status_code == 409


def test_register_invalid_email(client):
    assert register(client, email="not-an-email").status_code == 422


def test_register_short_password(client):
    assert register(client, password="123").status_code == 422


def test_login_success(client):
    register(client)
    response = login(client)
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_wrong_password(client):
    register(client)
    assert login(client, password="wrongpass").status_code == 401


def test_login_unknown_email(client):
    assert login(client, email="nobody@example.com").status_code == 401


def test_me_requires_token(client):
    assert client.get(ME_URL).status_code == 401


def test_me_with_token(client):
    register(client)
    token = login(client).json()["access_token"]
    response = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == USER["email"]


def test_me_with_invalid_token(client):
    response = client.get(ME_URL, headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401