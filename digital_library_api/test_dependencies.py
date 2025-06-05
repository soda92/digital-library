import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect  # <--- Import inspect
from sqlalchemy.orm import sessionmaker

from .json_api import app, get_db  # Import the FastAPI app and the dependency
from .database import (
    Base,
    create_db_tables,
    User as DBUser,
    Book as DBBook,  # <--- Import DBBook as well if you want to see it
)

from .test_json_api import db_session


def test_inspect_database_tables(db_session):  # noqa: F811
    """Test to inspect and list all tables in the test database."""
    # The db_session fixture ensures tables are created.
    # We can get the engine from the session.
    db_engine = (
        db_session.get_bind()
    )  # Or directly use the global `engine` if preferred

    # Create an inspector object
    inspector = inspect(db_engine)

    # Get table names
    table_names = inspector.get_table_names()

    # You can add assertions if you expect specific tables
    assert "users" in table_names
    assert "books" in table_names

    # If you want to inspect columns of a specific table (e.g., 'users'):
    if "users" in table_names:
        print("\nColumns in 'users' table:")
        columns = inspector.get_columns("users")
        for column in columns:
            print(f"- {column['name']} (type: {column['type']})")
