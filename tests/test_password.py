from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import settings
from app.core.security import generate_refresh_token
from app.modules.auth import repository
from app.modules.auth.tasks import _build_reset_email
from app.modules.users.models import User

API = "/api/v1"
EMAIL = "khaled@example.com"
PASSWORD = "Sup3r-Secret-Pass"
NEW_PASSWORD = "An0ther-Strong-Pass"


def register_and_login(client):
    client.post(
        f"{API}/auth/register",
        json={"email": EMAIL, "full_name": "Khaled", "password": PASSWORD},
    )
    return client.post(
        f"{API}/auth/login", data={"username": EMAIL, "password": PASSWORD}
    ).json()


def login(client, password):
    return client.post(f"{API}/auth/login", data={"username": EMAIL, "password": password})


def make_reset_token(db):
    user = db.scalars(select(User)).one()
    raw, token_hash = generate_refresh_token()
    repository.create_reset_token(
        db,
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db.commit()
    return raw


def test_change_password_success_and_revokes_sessions(client):
    tokens = register_and_login(client)
    response = client.post(
        f"{API}/auth/change-password",
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 204
    assert login(client, PASSWORD).status_code == 401
    assert login(client, NEW_PASSWORD).status_code == 200
    old = client.post(
        f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert old.status_code == 401


def test_change_password_wrong_current(client):
    tokens = register_and_login(client)
    response = client.post(
        f"{API}/auth/change-password",
        json={"current_password": "wrong-password", "new_password": NEW_PASSWORD},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 401


def test_change_password_rejects_weak_new_password(client):
    tokens = register_and_login(client)
    response = client.post(
        f"{API}/auth/change-password",
        json={"current_password": PASSWORD, "new_password": "password1"},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 422


def test_change_password_requires_auth(client):
    response = client.post(
        f"{API}/auth/change-password",
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert response.status_code == 401


def test_forgot_password_same_response_for_unknown_email(client):
    register_and_login(client)
    known = client.post(f"{API}/auth/forgot-password", json={"email": EMAIL})
    unknown = client.post(
        f"{API}/auth/forgot-password", json={"email": "ghost@example.com"}
    )
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()


def test_reset_password_flow(client, db):
    register_and_login(client)
    raw = make_reset_token(db)
    response = client.post(
        f"{API}/auth/reset-password", json={"token": raw, "new_password": NEW_PASSWORD}
    )
    assert response.status_code == 204
    assert login(client, NEW_PASSWORD).status_code == 200
    assert login(client, PASSWORD).status_code == 401


def test_reset_token_is_single_use(client, db):
    register_and_login(client)
    raw = make_reset_token(db)
    body = {"token": raw, "new_password": NEW_PASSWORD}
    assert client.post(f"{API}/auth/reset-password", json=body).status_code == 204
    assert client.post(f"{API}/auth/reset-password", json=body).status_code == 401


def test_reset_with_expired_token(client, db):
    register_and_login(client)
    raw = make_reset_token(db)
    row = db.scalars(select(repository.PasswordResetToken)).one()
    row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    response = client.post(
        f"{API}/auth/reset-password", json={"token": raw, "new_password": NEW_PASSWORD}
    )
    assert response.status_code == 401


def test_reset_with_unknown_token(client):
    response = client.post(
        f"{API}/auth/reset-password",
        json={"token": "x" * 40, "new_password": NEW_PASSWORD},
    )
    assert response.status_code == 401


def test_reset_clears_lockout(client, db):
    register_and_login(client)
    for _ in range(5):
        login(client, "wrong-password")
    assert login(client, PASSWORD).status_code == 401  # مقفول
    raw = make_reset_token(db)
    client.post(
        f"{API}/auth/reset-password", json={"token": raw, "new_password": NEW_PASSWORD}
    )
    assert login(client, NEW_PASSWORD).status_code == 200

def test_forgot_password_queues_email_for_known_user(client, mock_reset_email):
    register_and_login(client)
    response = client.post(f"{API}/auth/forgot-password", json={"email": EMAIL})
    assert response.status_code == 200
    mock_reset_email.assert_called_once()
    to_email, reset_link = mock_reset_email.call_args.args
    assert to_email == EMAIL
    assert reset_link.startswith(f"{settings.FRONTEND_URL}/reset-password?token=")


def test_forgot_password_does_not_queue_email_for_unknown_email(client, mock_reset_email):
    register_and_login(client)
    response = client.post(
        f"{API}/auth/forgot-password", json={"email": "ghost@example.com"}
    )
    assert response.status_code == 200
    mock_reset_email.assert_not_called()


def test_link_from_email_resets_password(client, mock_reset_email):
    register_and_login(client)
    client.post(f"{API}/auth/forgot-password", json={"email": EMAIL})
    _, reset_link = mock_reset_email.call_args.args
    token = reset_link.split("token=")[1]
    response = client.post(
        f"{API}/auth/reset-password", json={"token": token, "new_password": NEW_PASSWORD}
    )
    assert response.status_code == 204
    assert login(client, NEW_PASSWORD).status_code == 200


def test_reset_email_contains_recipient_and_link():
    link = "http://localhost:3000/reset-password?token=abc123"
    msg = _build_reset_email("user@example.com", link)
    assert msg["To"] == "user@example.com"
    assert link in msg.get_body(preferencelist=("plain",)).get_content()
    assert link in msg.get_body(preferencelist=("html",)).get_content()

def test_forgot_password_survives_broker_outage(client, mock_reset_email):
    register_and_login(client)
    mock_reset_email.side_effect = ConnectionError("redis is down")
    response = client.post(f"{API}/auth/forgot-password", json={"email": EMAIL})
    assert response.status_code == 200
    assert response.json() == {"message": "If the email exists, a reset link has been sent."}
