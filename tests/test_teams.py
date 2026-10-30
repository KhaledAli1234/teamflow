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


def make_team(client, headers, name="Backend Team"):
    return client.post(f"{API}/teams", json={"name": name}, headers=headers)


def test_create_team_makes_creator_admin(client):
    admin = make_user(client, "admin@example.com")
    response = make_team(client, admin)
    assert response.status_code == 201
    res = client.get(f"{API}/teams/1/members", headers=admin).json()
    assert res["total"] == 1
    assert res["page"] == 1
    assert res["page_size"] == 20
    members = res["items"]
    assert len(members) == 1
    assert members[0]["role"] == "admin"


def test_teams_require_auth(client):
    assert client.get(f"{API}/teams").status_code == 401


def test_list_only_my_teams(client):
    a = make_user(client, "a@example.com")
    b = make_user(client, "b@example.com")
    make_team(client, a, "A team")
    make_team(client, b, "B team")
    res = client.get(f"{API}/teams", headers=a).json()
    assert res["total"] == 1
    assert res["page"] == 1
    assert res["page_size"] == 20
    names = [t["name"] for t in res["items"]]
    assert names == ["A team"]


def test_non_member_cannot_see_team(client):
    admin = make_user(client, "admin@example.com")
    outsider = make_user(client, "out@example.com")
    team_id = make_team(client, admin).json()["id"]
    assert client.get(f"{API}/teams/{team_id}", headers=outsider).status_code == 404


def test_admin_adds_member(client):
    admin = make_user(client, "admin@example.com")
    make_user(client, "member@example.com")
    team_id = make_team(client, admin).json()["id"]
    response = client.post(
        f"{API}/teams/{team_id}/members",
        json={"email": "member@example.com"},
        headers=admin,
    )
    assert response.status_code == 201
    assert response.json()["role"] == "member"


def test_add_duplicate_member(client):
    admin = make_user(client, "admin@example.com")
    make_user(client, "member@example.com")
    team_id = make_team(client, admin).json()["id"]
    body = {"email": "member@example.com"}
    client.post(f"{API}/teams/{team_id}/members", json=body, headers=admin)
    response = client.post(f"{API}/teams/{team_id}/members", json=body, headers=admin)
    assert response.status_code == 409


def test_add_unknown_user(client):
    admin = make_user(client, "admin@example.com")
    team_id = make_team(client, admin).json()["id"]
    response = client.post(
        f"{API}/teams/{team_id}/members",
        json={"email": "ghost@example.com"},
        headers=admin,
    )
    assert response.status_code == 404


def test_member_cannot_update_team(client):
    admin = make_user(client, "admin@example.com")
    member = make_user(client, "member@example.com")
    team_id = make_team(client, admin).json()["id"]
    client.post(
        f"{API}/teams/{team_id}/members",
        json={"email": "member@example.com"},
        headers=admin,
    )
    response = client.patch(
        f"{API}/teams/{team_id}", json={"name": "Hacked"}, headers=member
    )
    assert response.status_code == 403


def test_admin_updates_team(client):
    admin = make_user(client, "admin@example.com")
    team_id = make_team(client, admin).json()["id"]
    response = client.patch(
        f"{API}/teams/{team_id}", json={"name": "Renamed"}, headers=admin
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


def test_last_admin_cannot_be_demoted(client):
    admin = make_user(client, "admin@example.com")
    team_id = make_team(client, admin).json()["id"]
    response = client.patch(
        f"{API}/teams/{team_id}/members/1", json={"role": "member"}, headers=admin
    )
    assert response.status_code == 403


def test_member_can_leave_team(client):
    admin = make_user(client, "admin@example.com")
    member = make_user(client, "member@example.com")
    team_id = make_team(client, admin).json()["id"]
    client.post(
        f"{API}/teams/{team_id}/members",
        json={"email": "member@example.com"},
        headers=admin,
    )
    response = client.delete(f"{API}/teams/{team_id}/members/2", headers=member)
    assert response.status_code == 204


def test_member_cannot_remove_others(client):
    admin = make_user(client, "admin@example.com")
    member = make_user(client, "member@example.com")
    team_id = make_team(client, admin).json()["id"]
    client.post(
        f"{API}/teams/{team_id}/members",
        json={"email": "member@example.com"},
        headers=admin,
    )
    response = client.delete(f"{API}/teams/{team_id}/members/1", headers=member)
    assert response.status_code == 403


def test_admin_deletes_team(client):
    admin = make_user(client, "admin@example.com")
    team_id = make_team(client, admin).json()["id"]
    assert client.delete(f"{API}/teams/{team_id}", headers=admin).status_code == 204
    assert client.get(f"{API}/teams/{team_id}", headers=admin).status_code == 404