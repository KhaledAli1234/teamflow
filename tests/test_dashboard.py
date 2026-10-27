API = "/api/v1"


def make_user(client, email):
    client.post(
        f"{API}/auth/register",
        json={"email": email, "full_name": email.split("@")[0], "password": "12345678"},
    )
    token = client.post(
        f"{API}/auth/login", data={"username": email, "password": "12345678"}
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


def add_task(client, admin, **body):
    return client.post(f"{API}/projects/1/tasks", json={"title": "T", **body}, headers=admin)


def test_dashboard_counts(client):
    admin, _ = setup(client)
    add_task(client, admin, assignee_id=2)
    add_task(client, admin, assignee_id=2)
    add_task(client, admin, due_date="2020-01-01")  # متأخرة
    client.patch(f"{API}/tasks/1/status", json={"status": "done"}, headers=admin)

    data = client.get(f"{API}/teams/1/dashboard", headers=admin).json()
    assert data["total_projects"] == 1
    assert data["total_tasks"] == 3
    assert data["completed_tasks"] == 1
    assert data["overdue_tasks"] == 1
    assert data["tasks_by_status"] == {"todo": 2, "in_progress": 0, "done": 1}
    assert data["projects"][0]["progress_percent"] == 33.3


def test_dashboard_workload(client):
    admin, _ = setup(client)
    add_task(client, admin, assignee_id=2)
    add_task(client, admin, assignee_id=2)
    client.patch(f"{API}/tasks/1/status", json={"status": "done"}, headers=admin)
    workload = client.get(f"{API}/teams/1/dashboard", headers=admin).json()["workload"]
    assert workload == [
        {"user_id": 2, "full_name": "member", "total_tasks": 2, "open_tasks": 1}
    ]


def test_empty_project_shows_zero_progress(client):
    admin, _ = setup(client)
    data = client.get(f"{API}/teams/1/dashboard", headers=admin).json()
    assert data["projects"][0]["total_tasks"] == 0
    assert data["projects"][0]["progress_percent"] == 0.0


def test_member_cannot_view_dashboard(client):
    _, member = setup(client)
    assert client.get(f"{API}/teams/1/dashboard", headers=member).status_code == 403


def test_outsider_cannot_view_dashboard(client):
    setup(client)
    outsider = make_user(client, "out@example.com")
    assert client.get(f"{API}/teams/1/dashboard", headers=outsider).status_code == 404


def test_project_progress_for_member(client):
    admin, member = setup(client)
    add_task(client, admin)
    add_task(client, admin)
    client.patch(f"{API}/tasks/1/status", json={"status": "done"}, headers=admin)
    data = client.get(f"{API}/projects/1/progress", headers=member).json()
    assert data["progress_percent"] == 50.0
    assert data["done_tasks"] == 1