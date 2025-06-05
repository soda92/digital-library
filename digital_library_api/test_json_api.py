import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect # <--- Import inspect
from sqlalchemy.orm import sessionmaker

from .json_api import app, get_db  # Import the FastAPI app and the dependency
from .database import (
    Base,
    create_db_tables,
    User as DBUser,
    Book as DBBook, # <--- Import DBBook as well if you want to see it
)

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
    create_db_tables(engine=engine) # This creates 'users' and 'books' tables
    db = TestingSessionLocal() # type: ignore
    # db.commit() # Not strictly necessary here if no initial data is added by the fixture itself
    yield db  # Provide the session to the test
    db.close()
    Base.metadata.drop_all(bind=engine)  # Drop tables


# You might not need to explicitly use db_session fixture in tests
# because the dependency override handles the session.
# The fixture is mainly here to ensure tables are created/dropped.

# --- Basic Test Examples ---


def test_create_user(db_session):
    """Test user registration endpoint."""
    response = client.post(
        "/users/", json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data
    # Password should not be returned
    assert "hashed_password" not in data

    # --- Debugging DB Inspection ---
    # Set your breakpoint here
    # For example, using pdb:
    # import pdb; pdb.set_trace()

    # Now you can use db_session to query the database
    user_in_db = db_session.query(DBUser).filter(DBUser.username == "testuser").first()
    assert user_in_db is not None
    assert user_in_db.username == "testuser"
    assert user_in_db.id == data["id"]
    # You can inspect user_in_db.hashed_password if needed for debugging,
    # though it's good practice not to assert its exact value in tests
    # unless you're specifically testing the hashing mechanism.
    print(f"User from DB: ID={user_in_db.id}, Username={user_in_db.username}")


def test_create_user_existing_username():
    """Test registration with an already existing username."""
    # First, create the user
    client.post(
        "/users/", json={"username": "duplicateuser", "password": "password123"}
    )
    # Then, try to create again with the same username
    response = client.post(
        "/users/", json={"username": "duplicateuser", "password": "anotherpassword"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}


def test_login_for_access_token():
    """Test user login endpoint."""
    # First, create a user to log in with
    client.post("/users/", json={"username": "loginuser", "password": "loginpassword"})
    # Then, attempt to log in
    response = client.post(
        "/token",
        data={
            "username": "loginuser",
            "password": "loginpassword",
        },  # Note: form-urlencoded data
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials():
    """Test login with incorrect username or password."""
    # Ensure no user exists with this name
    response = client.post(
        "/token", data={"username": "nonexistent", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


# Add more tests for other endpoints (books, borrow, return)

def test_inspect_database_tables(db_session):
    """Test to inspect and list all tables in the test database."""
    # The db_session fixture ensures tables are created.
    # We can get the engine from the session.
    db_engine = db_session.get_bind() # Or directly use the global `engine` if preferred

    # Create an inspector object
    inspector = inspect(db_engine)

    # Get table names
    table_names = inspector.get_table_names()

    print("\nTables in the test database:")
    for name in table_names:
        print(f"- {name}")

    # You can add assertions if you expect specific tables
    assert "users" in table_names
    assert "books" in table_names
    # Add more assertions for other tables if you have them

    # If you want to inspect columns of a specific table (e.g., 'users'):
    if "users" in table_names:
        print("\nColumns in 'users' table:")
        columns = inspector.get_columns("users")
        for column in columns:
            print(f"- {column['name']} (type: {column['type']})")

    # You can put a breakpoint here to explore `inspector` or `table_names`
    # import pdb; pdb.set_trace()
