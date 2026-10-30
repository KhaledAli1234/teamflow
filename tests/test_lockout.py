from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.modules.users.models import User

API = "/api/v1"
EMAIL = "khaled@example.com"
PASSWORD = "Sup3r-Secret-Pass"


def setup_user(client):
    client.post(
        f"{API}/auth/register",
        json={"email": EMAIL, "full_name": "Khaled", "password": PASSWORD},
    )


def attempt(client, password):
    return client.post(
        f"{API}/auth/login", data={"username": EMAIL, "password": password}
    )


def test_account_locks_after_five_failures(client):
    setup_user(client)
    for _ in range(5):
        assert attempt(client, "wrong-password").status_code == 401
    # حتى الباسورد الصح بيترفض وهو مقفول
    assert attempt(client, PASSWORD).status_code == 401


def test_successful_login_resets_counter(client, db):
    setup_user(client)
    for _ in range(3):
        attempt(client, "wrong-password")
    assert attempt(client, PASSWORD).status_code == 200
    assert db.scalars(select(User)).one().failed_login_attempts == 0


def test_lock_expires(client, db):
    setup_user(client)
    for _ in range(5):
        attempt(client, "wrong-password")
    user = db.scalars(select(User)).one()
    user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    assert attempt(client, PASSWORD).status_code == 200