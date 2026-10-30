# TeamFlow — Backend API

A production-grade project & task management REST API built with **Python 3.10**, **FastAPI**, **PostgreSQL**, **SQLAlchemy 2.0**, and **Alembic**. Inspired by Trello/Jira.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.110+ |
| ORM | SQLAlchemy 2.0 (mapped columns) |
| Database | PostgreSQL 16 |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | Argon2id · JWT (HS256) · Refresh token rotation |
| Rate limiting | SlowAPI |
| Testing | pytest + httpx |
| Containerization | Docker + Docker Compose |
| CI | GitHub Actions |

---

## Architecture

```
app/
├── core/          # Config, logging, middleware, rate limiting, security utils
├── common/        # Shared exceptions, dependencies, schemas (Page[T], UserSummary)
├── db/            # SQLAlchemy session factory, declarative base
└── modules/
    ├── auth/          # Login, register, JWT, refresh rotation, password reset
    ├── users/         # GET /me, PATCH /me
    ├── teams/         # Teams + member management (role-based)
    ├── projects/      # Projects + project member management
    ├── tasks/         # Tasks with filters, pagination, status transitions
    ├── comments/      # Task comments
    ├── activity/      # Immutable activity log per project
    ├── dashboard/     # Team & project progress stats
    └── notifications/ # Per-user in-app notifications
```

**Request flow:** `Router → Service → Repository → SQLAlchemy ORM → PostgreSQL`

**Transaction ownership:** Repositories only `flush()`. Services own `commit()` — guaranteeing that multi-step operations (task created + activity logged + notification queued) land atomically in one transaction.

---

## Permission Model

| Role | Scope | Can do |
|------|-------|--------|
| `ADMIN` | Team | Everything: manage members, projects, tasks |
| `PROJECT_MANAGER` | Team | Create/update projects and tasks; add project members |
| `MEMBER` | Team | View and work on tasks they're assigned to |

Projects also have their own member list. Managers/admins see all projects in a team; regular members see only the projects they're assigned to.

---

## Key Design Decisions

- **Refresh token rotation with family revocation:** Every refresh invalidates the old token and issues a new one. Token reuse (replay attack) revokes the entire family for that user.
- **Argon2id** for password hashing — the current OWASP recommendation over bcrypt.
- **Account lockout** after configurable failed attempts (`MAX_FAILED_LOGINS`, `LOCKOUT_MINUTES`).
- **Timing attack mitigation:** `forgot_password` always takes the same time whether the email exists or not.
- **Race condition protection:** Admin role demotions and member removals use `SELECT ... FOR UPDATE` to prevent a concurrent request from leaving a team with zero admins.
- **LIKE injection protection:** Search queries escape `%`, `_`, and `\` before building LIKE predicates.

---

## Running Locally

### Prerequisites
- Docker + Docker Compose

### 1. Clone and configure

```bash
git clone <repo-url>
cd teamflow_backend
cp .env.example .env
# Edit .env: set SECRET_KEY to a random 32+ char string
```

### 2. Start services

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 3. Run without Docker (development)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Start PostgreSQL separately (or use docker compose up db)
alembic upgrade head

uvicorn app.main:app --reload
```

---

## Running Tests

```bash
# Requires the test database to exist: psql -c "CREATE DATABASE teamflow_test;"
pytest -v
```

The test suite uses a dedicated `teamflow_test` database and rolls back each test in a transaction — no data leakage between tests.

---

## Environment Variables

See [`.env.example`](.env.example) for all variables with comments. Key ones:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | PostgreSQL DSN (required) |
| `SECRET_KEY` | — | JWT signing key, min 32 chars (required) |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Short-lived JWT |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `MAX_FAILED_LOGINS` | `5` | Attempts before lockout |
| `LOCKOUT_MINUTES` | `15` | Lockout duration |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed origins |

---

## API Overview

| Resource | Endpoints |
|----------|-----------|
| Auth | POST /register, /login, /refresh, /logout, /logout-all, /forgot-password, /reset-password, /change-password |
| Users | GET /users/me, PATCH /users/me |
| Teams | CRUD /teams, /teams/{id}/members |
| Projects | CRUD /teams/{id}/projects, /projects/{id}/members |
| Tasks | CRUD /projects/{id}/tasks, PATCH /tasks/{id}/status |
| Comments | CRUD /tasks/{id}/comments |
| Activity | GET /projects/{id}/activity |
| Dashboard | GET /teams/{id}/dashboard, /projects/{id}/progress |
| Notifications | GET /notifications, PATCH /notifications/{id}/read, POST /notifications/read-all |

All list endpoints are paginated (`?page=1&page_size=20`).

---

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`):
1. Spins up PostgreSQL as a service container
2. Runs `alembic upgrade head`
3. Asserts `alembic check` (no undetected schema drift)
4. Runs `pytest -v`

---

## Known Limitations / Future Work

- **Email sending:** `forgot_password` logs the reset token but doesn't send email. Requires integrating `fastapi-mail` or SendGrid.
- **Rate limiter:** Uses in-memory SlowAPI storage — not suitable for multi-worker deployments. Switch to `storage_uri="redis://..."` for production.
- **File uploads:** No attachment support on tasks (common PM feature).
- **Superuser role:** No system-level admin; roles are team-scoped only.
- **Soft delete:** All deletes are hard deletes with cascade.
