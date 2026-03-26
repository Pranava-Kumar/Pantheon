import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from pantheon.api.main import app
from pantheon.db.session import get_db
from pantheon.db.models import User
from pantheon.auth.utils import get_password_hash
from pantheon.auth.jwt_handler import create_access_token
from unittest.mock import patch

# Setup in-memory SQLite for testing
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)

@pytest.fixture(autouse=True)
def mock_run_analysis():
    with patch("pantheon.jobs.daily_analysis.run_daily_analysis") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        yield session
    app.dependency_overrides[get_db] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_trigger_without_auth(client: TestClient):
    response = client.post("/api/v1/trigger")
    assert response.status_code == 401

def test_get_token_success(client: TestClient, session: Session):
    # Create a test user
    hashed_password = get_password_hash("testpassword")
    user = User(username="testuser", email="test@example.com", hashed_password=hashed_password)
    session.add(user)
    session.commit()
    
    # Try to login
    response = client.post(
        "/api/v1/token",
        data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_get_token_invalid_password(client: TestClient, session: Session):
    # Create a test user
    hashed_password = get_password_hash("testpassword")
    user = User(username="testuser", email="test@example.com", hashed_password=hashed_password)
    session.add(user)
    session.commit()
    
    # Try to login with wrong password
    response = client.post(
        "/api/v1/token",
        data={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_users_me_success(client: TestClient, session: Session):
    # Create a test user
    hashed_password = get_password_hash("testpassword")
    user = User(username="testuser", email="test@example.com", hashed_password=hashed_password)
    session.add(user)
    session.commit()
    
    # Get token
    token = create_access_token({"sub": "testuser"})
    
    # Get /users/me
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
    assert response.json()["email"] == "test@example.com"

def test_trigger_with_auth(client: TestClient, session: Session):
    # Create a test user
    hashed_password = get_password_hash("testpassword")
    user = User(username="testuser", email="test@example.com", hashed_password=hashed_password)
    session.add(user)
    session.commit()
    
    # Get token
    token = create_access_token({"sub": "testuser"})
    
    # Trigger analysis (will be accepted)
    response = client.post(
        "/api/v1/trigger",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
