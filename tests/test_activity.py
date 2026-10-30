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


def setup(client):
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


def actions(client, headers):
    res = client.get(f"{API}/projects/1/activity", headers=headers).json()
    return [entry["action"] for entry in res["items"]]


def test_task_creation_is_logged(client):
    admin, _ = setup(client)
    client.post(f"{API}/projects/1/tasks", json={"title": "T"}, headers=admin)
    res = client.get(f"{API}/projects/1/activity", headers=admin).json()
    assert res["total"] == 1
    assert res["page"] == 1
    assert res["page_size"] == 20
    assert actions(client, admin) == ["task.created"]


def test_status_change_is_logged_with_details(client):
    admin, member = setup(client)
    client.post(
        f"{API}/projects/1/tasks", json={"title": "T", "assignee_id": 2}, headers=admin
    )
    client.patch(f"{API}/tasks/1/status", json={"status": "done"}, headers=member)
    res = client.get(f"{API}/projects/1/activity", headers=admin).json()
    logs = res["items"]
    assert res["total"] == 2
    assert logs[0]["action"] == "task.status_changed"
    assert logs[0]["actor_id"] == 2
    assert logs[0]["details"] == {"from": "todo", "to": "done"}


def test_assignment_is_logged(client):
    admin, _ = setup(client)
    client.post(f"{API}/projects/1/tasks", json={"title": "T"}, headers=admin)
    client.patch(f"{API}/tasks/1", json={"assignee_id": 2}, headers=admin)
    assert "task.assigned" in actions(client, admin)


def test_comment_is_logged(client):
    admin, _ = setup(client)
    client.post(f"{API}/projects/1/tasks", json={"title": "T"}, headers=admin)
    client.post(f"{API}/tasks/1/comments", json={"body": "hi"}, headers=admin)
    assert "comment.added" in actions(client, admin)


def test_outsider_cannot_see_activity(client):
    setup(client)
    outsider = make_user(client, "out@example.com")
    response = client.get(f"{API}/projects/1/activity", headers=outsider)
    assert response.status_code == 404