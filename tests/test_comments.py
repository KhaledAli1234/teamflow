API = "/api/v1"


def make_user(client, email):
    client.post(
        f"{API}/auth/register",
        json={"email": email, "full_name": "User", "password": "Sup3r-Secret-Pass"},
    )
    token = client.post(
        f"{API}/auth/login", data={"username": email, "password": "Sup3r-Secret-Pass"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def setup_task(client):
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
    client.post(f"{API}/projects/1/tasks", json={"title": "Task"}, headers=admin)
    return admin, member


def comment(client, headers, body="Hello"):
    return client.post(f"{API}/tasks/1/comments", json={"body": body}, headers=headers)


def test_member_adds_comment(client):
    _, member = setup_task(client)
    response = comment(client, member)
    assert response.status_code == 201
    assert response.json()["author_id"] == 2


def test_outsider_cannot_comment(client):
    setup_task(client)
    outsider = make_user(client, "out@example.com")
    assert comment(client, outsider).status_code == 404


def test_empty_comment_rejected(client):
    admin, _ = setup_task(client)
    assert comment(client, admin, body="").status_code == 422


def test_list_comments(client):
    admin, member = setup_task(client)
    comment(client, admin, "one")
    comment(client, member, "two")
    res = client.get(f"{API}/tasks/1/comments", headers=admin).json()
    assert res["total"] == 2
    assert res["page"] == 1
    assert res["page_size"] == 20
    bodies = [c["body"] for c in res["items"]]
    assert bodies == ["one", "two"]


def test_author_edits_own_comment(client):
    _, member = setup_task(client)
    comment(client, member)
    response = client.patch(f"{API}/comments/1", json={"body": "Edited"}, headers=member)
    assert response.status_code == 200
    assert response.json()["body"] == "Edited"


def test_cannot_edit_others_comment(client):
    admin, member = setup_task(client)
    comment(client, member)
    response = client.patch(f"{API}/comments/1", json={"body": "X"}, headers=admin)
    assert response.status_code == 403


def test_manager_can_delete_others_comment(client):
    admin, member = setup_task(client)
    comment(client, member)
    assert client.delete(f"{API}/comments/1", headers=admin).status_code == 204


def test_member_cannot_delete_others_comment(client):
    admin, member = setup_task(client)
    comment(client, admin)
    assert client.delete(f"{API}/comments/1", headers=member).status_code == 403