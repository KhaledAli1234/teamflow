API = "/api/v1"


def make_user(client, email, name="User"):
    client.post(
        f"{API}/auth/register",
        json={"email": email, "full_name": name, "password": "Sup3r-Secret-Pass"},
    )
    token = client.post(
        f"{API}/auth/login", data={"username": email, "password": "Sup3r-Secret-Pass"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def setup_project(client):
    """admin (id=1) + member (id=2) في فريق 1 ومشروع 1."""
    admin = make_user(client, "admin@example.com")
    member = make_user(client, "member@example.com")
    client.post(f"{API}/teams", json={"name": "T"}, headers=admin)
    client.post(
        f"{API}/teams/1/members", json={"email": "member@example.com"}, headers=admin
    )
    client.post(f"{API}/teams/1/projects", json={"name": "P"}, headers=admin)
    client.post(
        f"{API}/projects/1/members", json={"email": "member@example.com"}, headers=admin
    )
    return admin, member


# ---------- PATCH /users/me ----------

def test_update_me_changes_and_cleans_name(client):
    headers = make_user(client, "a@example.com")
    res = client.patch(
        f"{API}/users/me", json={"full_name": "  New    Name "}, headers=headers
    )
    assert res.status_code == 200
    assert res.json()["full_name"] == "New Name"
    assert client.get(f"{API}/users/me", headers=headers).json()["full_name"] == "New Name"


def test_update_me_rejects_empty_name(client):
    headers = make_user(client, "a@example.com")
    res = client.patch(f"{API}/users/me", json={"full_name": "   "}, headers=headers)
    assert res.status_code == 422


def test_update_me_ignores_email_and_sensitive_fields(client):
    headers = make_user(client, "a@example.com")
    res = client.patch(
        f"{API}/users/me",
        json={"full_name": "Ok", "email": "hacker@example.com", "is_active": False},
        headers=headers,
    )
    assert res.status_code == 200
    me = client.get(f"{API}/users/me", headers=headers).json()
    assert me["email"] == "a@example.com"
    assert me["is_active"] is True


def test_update_me_requires_auth(client):
    res = client.patch(f"{API}/users/me", json={"full_name": "X"})
    assert res.status_code == 401


# ---------- WWW-Authenticate ----------

def test_401_includes_www_authenticate_header(client):
    res = client.get(f"{API}/users/me")
    assert res.status_code == 401
    assert res.headers.get("www-authenticate") == "Bearer"


def test_bad_login_includes_www_authenticate_header(client):
    res = client.post(
        f"{API}/auth/login", data={"username": "no@example.com", "password": "whatever123"}
    )
    assert res.status_code == 401
    assert res.headers.get("www-authenticate") == "Bearer"


# ---------- Project self-leave ----------

def test_member_can_leave_project(client):
    _, member = setup_project(client)
    res = client.delete(f"{API}/projects/1/members/2", headers=member)
    assert res.status_code == 204


def test_member_cannot_remove_another_member(client):
    admin, member = setup_project(client)
    res = client.delete(f"{API}/projects/1/members/1", headers=member)
    assert res.status_code == 403


def test_manager_can_remove_member(client):
    admin, _ = setup_project(client)
    res = client.delete(f"{API}/projects/1/members/2", headers=admin)
    assert res.status_code == 204


def test_leaving_twice_returns_404(client):
    _, member = setup_project(client)
    client.delete(f"{API}/projects/1/members/2", headers=member)
    # بعد الخروج مبقاش له وصول للمشروع → 404 أو Member not found
    res = client.delete(f"{API}/projects/1/members/2", headers=member)
    assert res.status_code == 404


def test_outsider_cannot_leave_project(client):
    setup_project(client)
    outsider = make_user(client, "out@example.com")
    res = client.delete(f"{API}/projects/1/members/3", headers=outsider)
    assert res.status_code == 404


# ---------- Pagination ----------

def _make_teams(client, headers, count):
    for i in range(count):
        client.post(f"{API}/teams", json={"name": f"Team {i}"}, headers=headers)


def test_teams_pagination_shape_and_pages(client):
    headers = make_user(client, "a@example.com")
    _make_teams(client, headers, 3)

    first = client.get(f"{API}/teams", headers=headers, params={"page_size": 2}).json()
    assert set(first) == {"items", "total", "page", "page_size"}
    assert first["total"] == 3
    assert first["page"] == 1
    assert first["page_size"] == 2
    assert len(first["items"]) == 2

    second = client.get(
        f"{API}/teams", headers=headers, params={"page": 2, "page_size": 2}
    ).json()
    assert len(second["items"]) == 1
    assert second["total"] == 3

    ids = {t["id"] for t in first["items"]} | {t["id"] for t in second["items"]}
    assert len(ids) == 3  # مفيش تكرار بين الصفحات


def test_page_beyond_last_is_empty(client):
    headers = make_user(client, "a@example.com")
    _make_teams(client, headers, 1)
    res = client.get(f"{API}/teams", headers=headers, params={"page": 5}).json()
    assert res["items"] == []
    assert res["total"] == 1


def test_invalid_pagination_params_rejected(client):
    headers = make_user(client, "a@example.com")
    for params in ({"page": 0}, {"page_size": 0}, {"page_size": 101}):
        res = client.get(f"{API}/teams", headers=headers, params=params)
        assert res.status_code == 422, params