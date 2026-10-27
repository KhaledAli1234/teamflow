import pytest
from jwt import InvalidTokenError

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

API = "/api/v1"


def test_hash_is_argon2_and_verifies():
    hashed = hash_password("Sup3r-Secret-Pass")
    assert hashed.startswith("$argon2id$")
    assert verify_password("Sup3r-Secret-Pass", hashed)
    assert not verify_password("wrong-password", hashed)


def test_verify_with_invalid_hash_returns_false():
    assert verify_password("anything", "not-a-hash") is False


def test_access_token_roundtrip():
    payload = decode_access_token(create_access_token("5"))
    assert payload["sub"] == "5"
    assert payload["type"] == "access"


def test_garbage_token_rejected():
    with pytest.raises(InvalidTokenError):
        decode_access_token("garbage")


def test_common_password_rejected(client):
    response = client.post(
        f"{API}/auth/register",
        json={"email": "a@example.com", "full_name": "A", "password": "password1"},
    )
    assert response.status_code == 422


def test_name_is_cleaned(client):
    response = client.post(
        f"{API}/auth/register",
        json={"email": "a@example.com", "full_name": "  Khaled   Ali ", "password": "Sup3r-Secret-Pass"},
    )
    assert response.json()["full_name"] == "Khaled Ali"