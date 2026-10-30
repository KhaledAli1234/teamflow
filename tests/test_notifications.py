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


def notes(client, headers, **params):
    res = client.get(f"{API}/notifications", headers=headers, params=params).json()
    return res["items"]


def test_assignment_notifies_assignee(client):
    admin, member = setup(client)
    client.post(
        f"{API}/projects/1/tasks", json={"title": "T", "assignee_id": 2}, headers=admin
    )
    raw = client.get(f"{API}/notifications", headers=member).json()
    assert raw["total"] == 1
    assert raw["page"] == 1
    assert raw["page_size"] == 20
    result = raw["items"]
    assert len(result) == 1
    assert result[0]["type"] == "task.assigned"
    assert result[0]["is_read"] is False


def test_self_assignment_does_not_notify(client):
    admin, _ = setup(client)
    client.post(
        f"{API}/projects/1/tasks", json={"title": "T", "assignee_id": 1}, headers=admin
    )
    assert notes(client, admin) == []


def test_reassignment_notifies_new_assignee(client):
    admin, member = setup(client)
    client.post(f"{API}/projects/1/tasks", json={"title": "T"}, headers=admin)
    client.patch(f"{API}/tasks/1", json={"assignee_id": 2}, headers=admin)
    assert len(notes(client, member)) == 1


def test_comment_notifies_others_not_author(client):
    admin, member = setup(client)
    client.post(
        f"{API}/projects/1/tasks", json={"title": "T", "assignee_id": 2}, headers=admin
    )
    client.post(f"{API}/tasks/1/comments", json={"body": "hi"}, headers=member)
    admin_notes = notes(client, admin)
    assert [n["type"] for n in admin_notes] == ["comment.added"]
    # العضو علّق بنفسه، فمفيش إشعار تعليق ليه (عنده بس إشعار الإسناد)
    assert [n["type"] for n in notes(client, member)] == ["task.assigned"]


def test_mark_one_read_and_filter(client):
    admin, member = setup(client)
    client.post(
        f"{API}/projects/1/tasks", json={"title": "T", "assignee_id": 2}, headers=admin
    )
    response = client.patch(f"{API}/notifications/1/read", headers=member)
    assert response.status_code == 200
    assert response.json()["is_read"] is True
    assert notes(client, member, unread_only=True) == []


def test_cannot_read_someone_elses_notification(client):
    admin, _ = setup(client)
    client.post(
        f"{API}/projects/1/tasks", json={"title": "T", "assignee_id": 2}, headers=admin
    )
    assert client.patch(f"{API}/notifications/1/read", headers=admin).status_code == 404


def test_mark_all_read(client):
    admin, member = setup(client)
    for i in range(3):
        client.post(
            f"{API}/projects/1/tasks",
            json={"title": f"T{i}", "assignee_id": 2},
            headers=admin,
        )
    response = client.post(f"{API}/notifications/read-all", headers=member)
    assert response.json() == {"updated": 3}
    assert notes(client, member, unread_only=True) == []