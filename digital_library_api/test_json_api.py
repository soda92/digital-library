import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool  # Add this import
from sqlalchemy.orm import sessionmaker

from .json_api import app, get_db  # Import the FastAPI app and the dependency
from .database import (
    Base,
    create_db_tables,
    User as DBUser,
    Book as DBBook,  # <--- Import DBBook as well if you want to see it
)

# --- Test Database Setup ---
# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Use StaticPool for in-memory SQLite
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
@pytest.fixture(scope="function", autouse=True)
def db_session(request):  # Added request for potential unique naming if needed
    """Create a new database session for each test."""
    # Ensure a clean state and create tables for each test using the test engine
    Base.metadata.create_all(bind=engine)  # Create all tables
    db = TestingSessionLocal()
    try:
        yield db  # Provide the session to the test
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)  # Ensure tables are dropped after the test


@pytest.fixture(scope="function")
def test_user(db_session):
    """Creates a user in the DB and returns the user object and raw password."""
    username = "testfixtureuser"
    password = "testfixturepassword"

    response = client.post("/users/", json={"username": username, "password": password})
    assert response.status_code == 201, (
        f"Failed to create user for fixture: {response.json()}"
    )
    user_data = response.json()

    db_user = db_session.query(DBUser).filter(DBUser.id == user_data["id"]).first()
    assert db_user is not None, "User not found in DB after creation for fixture"
    return {
        "db_user": db_user,
        "password": password,
        "id": db_user.id,
        "username": db_user.username,
    }


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Provides authentication headers for a test user."""
    username = test_user["username"]
    password = test_user["password"]

    response = client.post("/token", data={"username": username, "password": password})
    assert response.status_code == 200, (
        f"Failed to get token for fixture: {response.json()}"
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# You might not need to explicitly use db_session fixture in tests
# because the dependency override handles the session.
# The fixture is mainly here to ensure tables are created/dropped.

# --- Basic Test Examples ---


# Helper function to create a book for tests, used by other tests
def create_book_via_api_util(
    auth_headers_param, title="Test Book", author="Test Author", isbn="1234567890123"
):
    book_data = {"title": title, "author": author, "isbn": isbn}
    response = client.post("/books/", json=book_data, headers=auth_headers_param)
    assert response.status_code == 201, (
        f"Helper failed to create book: {response.json()}"
    )
    return response.json()


def test_create_user():
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

# --- Book Endpoint Tests ---


def test_create_book_success(auth_headers):
    """Test successful book creation."""
    book_data = {"title": "New Book", "author": "New Author", "isbn": "9998887776665"}
    response = client.post("/books/", json=book_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == book_data["title"]
    assert data["author"] == book_data["author"]
    assert data["isbn"] == book_data["isbn"]
    assert "id" in data
    assert data["is_borrowed"] is False
    assert data["borrower_id"] is None
    assert data["borrower_username"] is None
    assert data["due_date"] is None


def test_create_book_duplicate_isbn(auth_headers):
    """Test creating a book with an existing ISBN."""
    isbn = "1112223334445"
    create_book_via_api_util(auth_headers, title="Original Book", isbn=isbn)

    duplicate_book_data = {
        "title": "Another Book",
        "author": "Another Author",
        "isbn": isbn,
    }
    response = client.post("/books/", json=duplicate_book_data, headers=auth_headers)
    assert response.status_code == 400
    assert response.json() == {"detail": f"Book with ISBN {isbn} already exists."}


def test_create_book_unauthenticated():
    """Test creating a book without authentication."""
    book_data = {
        "title": "Unauthorized Book",
        "author": "No Auth",
        "isbn": "0001112223334",
    }
    response = client.post("/books/", json=book_data)  # No headers
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_get_all_books_empty():
    """Test getting all books when the database is empty."""
    response = client.get("/books/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_all_books_with_data(auth_headers):
    """Test getting all books when books exist."""
    book1_data = create_book_via_api_util(
        auth_headers, title="Book One", isbn="1000000000001"
    )
    book2_data = create_book_via_api_util(
        auth_headers, title="Book Two", isbn="1000000000002"
    )

    response = client.get("/books/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    response_isbns = {b["isbn"] for b in data}
    assert book1_data["isbn"] in response_isbns
    assert book2_data["isbn"] in response_isbns


def test_get_book_success(auth_headers):
    """Test getting a single existing book."""
    created_book = create_book_via_api_util(
        auth_headers, title="Specific Book", isbn="2000000000001"
    )
    book_id = created_book["id"]

    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book_id
    assert data["title"] == "Specific Book"
    assert data["is_borrowed"] is False


def test_get_book_not_found():
    """Test getting a non-existent book."""
    response = client.get("/books/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_update_book_success(auth_headers):
    """Test successfully updating a book's details."""
    created_book = create_book_via_api_util(
        auth_headers, title="Old Title", author="Old Author", isbn="3000000000001"
    )
    book_id = created_book["id"]

    update_payload = {"title": "New Title", "author": "New Author"}
    response = client.put(f"/books/{book_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["author"] == "New Author"
    assert data["isbn"] == created_book["isbn"]  # ISBN not changed


def test_update_book_not_found():
    """Test updating a non-existent book."""
    response = client.put("/books/99998", json={"title": "Ghost Title"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_update_book_duplicate_isbn(auth_headers):
    """Test updating a book's ISBN to one that already exists."""
    book1 = create_book_via_api_util(auth_headers, isbn="3000000000011")
    book2 = create_book_via_api_util(auth_headers, isbn="3000000000012")

    response = client.put(f"/books/{book2['id']}", json={"isbn": book1["isbn"]})
    assert response.status_code == 400
    assert response.json() == {
        "detail": f"Another book with ISBN {book1['isbn']} already exists."
    }


def test_update_book_return_action(auth_headers, test_user):
    """Test 'returning' a book using PUT by setting is_borrowed to False."""
    book_to_borrow = create_book_via_api_util(auth_headers, isbn="3000000000021")
    book_id = book_to_borrow["id"]

    borrow_response = client.post(
        f"/books/{book_id}/borrow", json={"borrow_days": 7}, headers=auth_headers
    )
    assert borrow_response.status_code == 200
    assert borrow_response.json()["is_borrowed"] is True

    response = client.put(f"/books/{book_id}", json={"is_borrowed": False})
    assert response.status_code == 200
    data = response.json()
    assert data["is_borrowed"] is False
    assert data["borrower_id"] is None
    assert data["due_date"] is None
    assert data["borrower_username"] is None


def test_update_book_try_borrow_via_put(auth_headers):
    """Test attempting to borrow a book via PUT (should be disallowed)."""
    book_to_borrow = create_book_via_api_util(auth_headers, isbn="3000000000031")
    book_id = book_to_borrow["id"]

    update_payload = {"is_borrowed": True, "due_date": "2099-01-01"}
    response = client.put(f"/books/{book_id}", json=update_payload)
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Cannot borrow book using PUT. Use the /borrow endpoint."
    }


def test_delete_book_success(auth_headers):
    """Test successfully deleting a book."""
    created_book = create_book_via_api_util(auth_headers, isbn="4000000000001")
    book_id = created_book["id"]

    response = client.delete(f"/books/{book_id}")
    assert response.status_code == 204

    get_response = client.get(f"/books/{book_id}")
    assert get_response.status_code == 404


def test_delete_book_not_found():
    """Test deleting a non-existent book."""
    response = client.delete("/books/99997")
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


# --- Borrow and Return Endpoint Tests ---


def test_borrow_book_success(auth_headers, test_user):
    """Test successfully borrowing an available book."""
    book = create_book_via_api_util(auth_headers, isbn="5000000000001")
    book_id = book["id"]

    response = client.post(
        f"/books/{book_id}/borrow", json={"borrow_days": 7}, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_borrowed"] is True
    assert data["borrower_id"] == test_user["id"]
    assert data["borrower_username"] == test_user["username"]
    assert data["due_date"] is not None


def test_borrow_book_not_found(auth_headers):
    """Test borrowing a non-existent book."""
    response = client.post(
        "/books/99996/borrow", json={"borrow_days": 7}, headers=auth_headers
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_borrow_book_already_borrowed(auth_headers, test_user):
    """Test borrowing a book that is already borrowed."""
    book = create_book_via_api_util(auth_headers, isbn="5000000000002")
    book_id = book["id"]
    client.post(
        f"/books/{book_id}/borrow", json={"borrow_days": 7}, headers=auth_headers
    )  # First borrow

    response = client.post(
        f"/books/{book_id}/borrow", json={"borrow_days": 7}, headers=auth_headers
    )  # Attempt second borrow
    assert response.status_code == 400
    assert response.json() == {
        "detail": f"Book is already borrowed by {test_user['username']}"
    }


def test_borrow_book_unauthenticated(
    db_session, auth_headers
):  # auth_headers to create a book easily
    """Test borrowing a book without authentication."""
    book = create_book_via_api_util(
        auth_headers, isbn="5000000000003"
    )  # Create book with temp auth
    book_id = book["id"]

    response = client.post(
        f"/books/{book_id}/borrow", json={"borrow_days": 7}
    )  # No headers
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_return_book_success(auth_headers, test_user):
    """Test successfully returning a borrowed book."""
    book = create_book_via_api_util(auth_headers, isbn="6000000000001")
    book_id = book["id"]
    client.post(
        f"/books/{book_id}/borrow", json={"borrow_days": 7}, headers=auth_headers
    )  # Borrow it

    response = client.post(f"/books/{book_id}/return", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_borrowed"] is False
    assert data["borrower_id"] is None
    assert data["borrower_username"] is None
    assert data["due_date"] is None


def test_return_book_not_found(auth_headers):
    """Test returning a non-existent book."""
    response = client.post("/books/99995/return", headers=auth_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_return_book_not_borrowed(auth_headers):
    """Test returning a book that is not currently borrowed."""
    book = create_book_via_api_util(auth_headers, isbn="6000000000002")
    book_id = book["id"]

    response = client.post(f"/books/{book_id}/return", headers=auth_headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "Book is not currently borrowed"}


def test_return_book_unauthenticated(
    db_session, auth_headers
):  # auth_headers to create and borrow a book easily
    """Test returning a book without authentication."""
    book = create_book_via_api_util(auth_headers, isbn="6000000000003")  # Create book
    book_id = book["id"]
    client.post(
        f"/books/{book_id}/borrow", json={"borrow_days": 7}, headers=auth_headers
    )  # Borrow it

    response = client.post(f"/books/{book_id}/return")  # No headers
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
