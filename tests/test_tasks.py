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


def setup_project(client):
    """أدمن (id=1) + عضو (id=2) في الفريق والمشروع. بيرجّع (admin, member)."""
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


def make_task(client, headers, **overrides):
    body = {"title": "Design DB", **overrides}
    return client.post(f"{API}/projects/1/tasks", json=body, headers=headers)


def test_admin_creates_task(client):
    admin, _ = setup_project(client)
    response = make_task(client, admin, assignee_id=2, priority="high")
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "todo"
    assert body["priority"] == "high"
    assert body["assignee_id"] == 2


def test_member_cannot_create_task(client):
    _, member = setup_project(client)
    assert make_task(client, member).status_code == 403


def test_outsider_cannot_see_tasks(client):
    setup_project(client)
    outsider = make_user(client, "out@example.com")
    assert client.get(f"{API}/projects/1/tasks", headers=outsider).status_code == 404


def test_cannot_assign_non_project_member(client):
    admin, _ = setup_project(client)
    make_user(client, "other@example.com")
    client.post(
        f"{API}/teams/1/members", json={"email": "other@example.com"}, headers=admin
    )
    # id=3 عضو في الفريق بس مش في المشروع
    assert make_task(client, admin, assignee_id=3).status_code == 403


def test_member_changes_status_of_own_task(client):
    admin, member = setup_project(client)
    make_task(client, admin, assignee_id=2)
    response = client.patch(
        f"{API}/tasks/1/status", json={"status": "in_progress"}, headers=member
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_member_cannot_change_status_of_others_task(client):
    admin, member = setup_project(client)
    make_task(client, admin)  # من غير مسؤول
    response = client.patch(
        f"{API}/tasks/1/status", json={"status": "done"}, headers=member
    )
    assert response.status_code == 403


def test_member_cannot_edit_task(client):
    admin, member = setup_project(client)
    make_task(client, admin, assignee_id=2)
    response = client.patch(f"{API}/tasks/1", json={"title": "X"}, headers=member)
    assert response.status_code == 403


def test_admin_updates_task(client):
    admin, _ = setup_project(client)
    make_task(client, admin)
    response = client.patch(
        f"{API}/tasks/1", json={"title": "New", "priority": "low"}, headers=admin
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New"


def test_filter_by_status_and_search(client):
    admin, _ = setup_project(client)
    make_task(client, admin, title="Design DB")
    make_task(client, admin, title="Write tests")
    client.patch(f"{API}/tasks/2/status", json={"status": "done"}, headers=admin)

    done = client.get(f"{API}/projects/1/tasks?status=done", headers=admin).json()
    assert [t["title"] for t in done["items"]] == ["Write tests"]

    found = client.get(f"{API}/projects/1/tasks?search=design", headers=admin).json()
    assert [t["title"] for t in found["items"]] == ["Design DB"]


def test_pagination(client):
    admin, _ = setup_project(client)
    for i in range(5):
        make_task(client, admin, title=f"Task {i}")
    page = client.get(
        f"{API}/projects/1/tasks?page=2&page_size=2", headers=admin
    ).json()
    assert page["total"] == 5
    assert page["page"] == 2
    assert len(page["items"]) == 2


def test_admin_deletes_task(client):
    admin, _ = setup_project(client)
    make_task(client, admin)
    assert client.delete(f"{API}/tasks/1", headers=admin).status_code == 204
    assert client.get(f"{API}/tasks/1", headers=admin).status_code == 404