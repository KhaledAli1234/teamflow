from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.modules.auth.models import RefreshToken
from app.modules.users.models import User

API = "/api/v1"
EMAIL = "khaled@example.com"
PASSWORD = "Sup3r-Secret-Pass"


def login_tokens(client):
    client.post(
        f"{API}/auth/register",
        json={"email": EMAIL, "full_name": "Khaled", "password": PASSWORD},
    )
    return client.post(
        f"{API}/auth/login", data={"username": EMAIL, "password": PASSWORD}
    ).json()


def refresh(client, token):
    return client.post(f"{API}/auth/refresh", json={"refresh_token": token})


def test_login_returns_both_tokens(client):
    tokens = login_tokens(client)
    assert tokens["access_token"]
    assert len(tokens["refresh_token"]) >= 20


def test_refresh_rotates_and_new_access_works(client):
    tokens = login_tokens(client)
    response = refresh(client, tokens["refresh_token"])
    assert response.status_code == 200
    new = response.json()
    assert new["refresh_token"] != tokens["refresh_token"]
    me = client.get(
        f"{API}/users/me", headers={"Authorization": f"Bearer {new['access_token']}"}
    )
    assert me.status_code == 200


def test_reusing_old_refresh_token_revokes_whole_family(client):
    tokens = login_tokens(client)
    new = refresh(client, tokens["refresh_token"]).json()
    assert refresh(client, tokens["refresh_token"]).status_code == 401
    assert refresh(client, new["refresh_token"]).status_code == 401


def test_unknown_refresh_token_rejected(client):
    assert refresh(client, "x" * 40).status_code == 401


def test_expired_refresh_token_rejected(client, db):
    tokens = login_tokens(client)
    row = db.scalars(select(RefreshToken)).one()
    row.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()
    assert refresh(client, tokens["refresh_token"]).status_code == 401


def test_logout_revokes_refresh_token(client):
    tokens = login_tokens(client)
    response = client.post(
        f"{API}/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 204
    assert refresh(client, tokens["refresh_token"]).status_code == 401


def test_logout_with_garbage_token_is_harmless(client):
    response = client.post(f"{API}/auth/logout", json={"refresh_token": "x" * 40})
    assert response.status_code == 204


def test_logout_all_revokes_every_session(client):
    first = login_tokens(client)
    second = client.post(
        f"{API}/auth/login", data={"username": EMAIL, "password": PASSWORD}
    ).json()
    response = client.post(
        f"{API}/auth/logout-all",
        headers={"Authorization": f"Bearer {second['access_token']}"},
    )
    assert response.status_code == 204
    assert refresh(client, first["refresh_token"]).status_code == 401
    assert refresh(client, second["refresh_token"]).status_code == 401


def test_disabled_user_cannot_refresh(client, db):
    tokens = login_tokens(client)
    user = db.scalars(select(User)).one()
    user.is_active = False
    db.commit()
    assert refresh(client, tokens["refresh_token"]).status_code == 401