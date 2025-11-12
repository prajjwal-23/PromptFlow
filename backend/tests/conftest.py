"""
Pytest configuration and fixtures for testing.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.auth import get_password_hash
from app.models.user import User
from app.models.workspace import Workspace, Membership, MembershipRole
from app.models.agent import Agent


# Test database setup - use in-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def db():
    """Create test database session."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database session for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user2(db_session):
    """Create a second test user."""
    user = User(
        email="test2@example.com",
        password_hash=get_password_hash("testpassword123"),
        full_name="Test User 2",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_workspace(db_session, test_user):
    """Create a test workspace."""
    workspace = Workspace(
        name="Test Workspace",
        description="A workspace for testing",
        created_by=str(test_user.id)
    )
    db_session.add(workspace)
    db_session.commit()
    db_session.refresh(workspace)
    
    # Create owner membership
    membership = Membership(
        user_id=str(test_user.id),
        workspace_id=str(workspace.id),
        role=MembershipRole.OWNER
    )
    db_session.add(membership)
    db_session.commit()
    
    return workspace


@pytest.fixture
def test_agent(db_session, test_workspace, test_user):
    """Create a test agent."""
    agent = Agent(
        workspace_id=str(test_workspace.id),
        name="Test Agent",
        description="A test agent",
        graph_json={
            "nodes": [
                {"id": "node1", "type": "input", "data": {"label": "Start"}},
                {"id": "node2", "type": "llm", "data": {"label": "LLM Node"}}
            ],
            "edges": [
                {"id": "edge1", "source": "node1", "target": "node2"}
            ]
        },
        created_by=str(test_user.id)
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user."""
    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def auth_headers2(client, test_user2):
    """Get authentication headers for second test user."""
    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user2.email,
            "password": "testpassword123"
        }
    )
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def workspace_with_member(db_session, test_workspace, test_user2):
    """Add a member to test workspace."""
    membership = Membership(
        user_id=str(test_user2.id),
        workspace_id=str(test_workspace.id),
        role=MembershipRole.MEMBER
    )
    db_session.add(membership)
    db_session.commit()
    db_session.refresh(membership)
    return membership