import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .json_api import app, get_db # Import the FastAPI app and the dependency
from .database import Base # Import Base for creating tables

# --- Test Database Setup ---
# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Dependency Override ---
# This function will be used to override the get_db dependency in json_api.py
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the dependency in the FastAPI app
app.dependency_overrides[get_db] = override_get_db

# --- Test Client ---
# Create a TestClient instance for your app
client = TestClient(app)

# --- Pytest Fixtures ---
# Fixture to create and drop tables for each test
@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for each test."""
    Base.metadata.create_all(bind=engine) # Create tables
    db = TestingSessionLocal()
    yield db # Provide the session to the test
    db.rollback() # Rollback any changes made during the test
    db.close()
    Base.metadata.drop_all(bind=engine) # Drop tables

# You might not need to explicitly use db_session fixture in tests
# because the dependency override handles the session.
# The fixture is mainly here to ensure tables are created/dropped.

# --- Basic Test Examples ---

def test_create_user():
    """Test user registration endpoint."""
    response = client.post(
        "/users/",
        json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data
    # Password should not be returned
    assert "hashed_password" not in data

def test_create_user_existing_username():
    """Test registration with an already existing username."""
    # First, create the user
    client.post(
        "/users/",
        json={"username": "duplicateuser", "password": "password123"}
    )
    # Then, try to create again with the same username
    response = client.post(
        "/users/",
        json={"username": "duplicateuser", "password": "anotherpassword"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}

def test_login_for_access_token():
    """Test user login endpoint."""
    # First, create a user to log in with
    client.post(
        "/users/",
        json={"username": "loginuser", "password": "loginpassword"}
    )
    # Then, attempt to log in
    response = client.post(
        "/token",
        data={"username": "loginuser", "password": "loginpassword"} # Note: form-urlencoded data
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials():
    """Test login with incorrect username or password."""
    # Ensure no user exists with this name
    response = client.post(
        "/token",
        data={"username": "nonexistent", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

# Add more tests for other endpoints (books, borrow, return)