API = "/api/v1"


def make_user(client, email):
    client.post(
        f"{API}/auth/register",
        json={"email": email, "full_name": "User", "password": "12345678"},
    )
    token = client.post(
        f"{API}/auth/login", data={"username": email, "password": "12345678"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def setup_team(client):
    """أدمن + عضو عادي في فريق واحد. بيرجّع (admin, member, team_id)."""
    admin = make_user(client, "admin@example.com")
    member = make_user(client, "member@example.com")
    team_id = client.post(f"{API}/teams", json={"name": "T"}, headers=admin).json()["id"]
    client.post(
        f"{API}/teams/{team_id}/members",
        json={"email": "member@example.com"},
        headers=admin,
    )
    return admin, member, team_id


def make_project(client, headers, team_id, **overrides):
    body = {"name": "Website", "status": "active", **overrides}
    return client.post(f"{API}/teams/{team_id}/projects", json=body, headers=headers)


def test_admin_creates_project(client):
    admin, _, team_id = setup_team(client)
    response = make_project(client, admin, team_id)
    assert response.status_code == 201
    assert response.json()["name"] == "Website"


def test_member_cannot_create_project(client):
    _, member, team_id = setup_team(client)
    assert make_project(client, member, team_id).status_code == 403


def test_outsider_cannot_create_project(client):
    admin, _, team_id = setup_team(client)
    outsider = make_user(client, "out@example.com")
    assert make_project(client, outsider, team_id).status_code == 404


def test_invalid_dates_rejected(client):
    admin, _, team_id = setup_team(client)
    response = make_project(
        client, admin, team_id, start_date="2026-12-01", due_date="2026-11-01"
    )
    assert response.status_code == 422


def test_project_manager_can_create(client):
    admin, member, team_id = setup_team(client)
    client.patch(
        f"{API}/teams/{team_id}/members/2",
        json={"role": "project_manager"},
        headers=admin,
    )
    assert make_project(client, member, team_id).status_code == 201


def test_member_sees_only_assigned_projects(client):
    admin, member, team_id = setup_team(client)
    make_project(client, admin, team_id, name="P1")
    make_project(client, admin, team_id, name="P2")
    assert client.get(f"{API}/teams/{team_id}/projects", headers=member).json() == []
    client.post(
        f"{API}/projects/1/members", json={"email": "member@example.com"}, headers=admin
    )
    names = [
        p["name"]
        for p in client.get(f"{API}/teams/{team_id}/projects", headers=member).json()
    ]
    assert names == ["P1"]


def test_admin_sees_all_projects(client):
    admin, _, team_id = setup_team(client)
    make_project(client, admin, team_id, name="P1")
    make_project(client, admin, team_id, name="P2")
    assert len(client.get(f"{API}/teams/{team_id}/projects", headers=admin).json()) == 2


def test_member_cannot_open_unassigned_project(client):
    admin, member, team_id = setup_team(client)
    make_project(client, admin, team_id)
    assert client.get(f"{API}/projects/1", headers=member).status_code == 404


def test_member_cannot_update_project(client):
    admin, member, team_id = setup_team(client)
    make_project(client, admin, team_id)
    client.post(
        f"{API}/projects/1/members", json={"email": "member@example.com"}, headers=admin
    )
    response = client.patch(f"{API}/projects/1", json={"name": "X"}, headers=member)
    assert response.status_code == 403


def test_admin_updates_project(client):
    admin, _, team_id = setup_team(client)
    make_project(client, admin, team_id)
    response = client.patch(
        f"{API}/projects/1", json={"status": "completed"}, headers=admin
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_cannot_add_non_team_member_to_project(client):
    admin, _, team_id = setup_team(client)
    make_user(client, "out@example.com")
    make_project(client, admin, team_id)
    response = client.post(
        f"{API}/projects/1/members", json={"email": "out@example.com"}, headers=admin
    )
    assert response.status_code == 404


def test_add_duplicate_project_member(client):
    admin, _, team_id = setup_team(client)
    make_project(client, admin, team_id)
    body = {"email": "member@example.com"}
    client.post(f"{API}/projects/1/members", json=body, headers=admin)
    assert (
        client.post(f"{API}/projects/1/members", json=body, headers=admin).status_code
        == 409
    )


def test_admin_deletes_project(client):
    admin, _, team_id = setup_team(client)
    make_project(client, admin, team_id)
    assert client.delete(f"{API}/projects/1", headers=admin).status_code == 204
    assert client.get(f"{API}/projects/1", headers=admin).status_code == 404