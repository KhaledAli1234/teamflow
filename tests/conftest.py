import os
os.environ["RATE_LIMIT_ENABLED"] = "false"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.teams import models as teams_models  # noqa: F401
from app.modules.users import models as users_models  # noqa: F401
from app.modules.projects import models as projects_models  # noqa: F401
from app.modules.tasks import models as tasks_models  # noqa: F401
from app.modules.comments import models as comments_models  # noqa: F401
from app.modules.activity import models as activity_models  # noqa: F401
from app.modules.notifications import models as notifications_models  # noqa: F401
from app.modules.auth import models as auth_models  # noqa: F401

TEST_DATABASE_URL = settings.DATABASE_URL.rsplit("/", 1)[0] + "/teamflow_test"

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        table_names = ", ".join(t.name for t in Base.metadata.sorted_tables)
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()