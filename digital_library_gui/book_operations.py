from sqlalchemy.orm import Session
from datetime import date, timedelta

from digital_library.database import Book as DBBook


def get_all_books(db_session: Session):
    """Fetches all books from the database."""
    return db_session.query(DBBook).all()


def get_book_by_id(db_session: Session, book_id: int):
    """Fetches a single book by its ID."""
    return db_session.query(DBBook).filter(DBBook.id == book_id).first()


def check_isbn_exists(db_session: Session, isbn: str, exclude_book_id: int = None):
    """Checks if an ISBN exists, optionally excluding a specific book ID."""
    query = db_session.query(DBBook).filter(DBBook.isbn == isbn)
    if exclude_book_id is not None:
        query = query.filter(DBBook.id != exclude_book_id)
    return query.first()


def add_new_book(db_session: Session, title: str, author: str, isbn: str):
    """Adds a new book to the database.

    Returns:
        Tuple (DBBook | None, str | None): (book_object, error_message)
    """
    if not title or not author or not isbn:
        return None, "All fields must be filled."

    if check_isbn_exists(db_session, isbn):
        return None, f"Book with ISBN {isbn} already exists."

    new_book = DBBook(title=title, author=author, isbn=isbn)
    db_session.add(new_book)
    db_session.commit()
    db_session.refresh(new_book)
    return new_book, None


def update_existing_book(db_session: Session, book_id: int, title: str, author: str, isbn: str):
    """Updates an existing book in the database.

    Returns:
        Tuple (DBBook | None, str | None): (book_object, error_message)
    """
    book_to_edit = get_book_by_id(db_session, book_id)
    if not book_to_edit:
        return None, "Book not found in database."

    if not title or not author or not isbn:
        return None, "All fields must be filled for editing."

    if check_isbn_exists(db_session, isbn, exclude_book_id=book_id):
        return None, f"Another book with ISBN {isbn} already exists."

    book_to_edit.title = title
    book_to_edit.author = author
    book_to_edit.isbn = isbn
    db_session.commit()
    db_session.refresh(book_to_edit)
    return book_to_edit, None


def delete_existing_book(db_session: Session, book_id: int):
    """Deletes a book from the database.

    Returns:
        Tuple (bool, str | None): (success_status, error_message)
    """
    book_to_delete = get_book_by_id(db_session, book_id)
    if not book_to_delete:
        return False, "Book not found in database for deletion."

    db_session.delete(book_to_delete)
    db_session.commit()
    return True, None


def borrow_selected_book(db_session: Session, book_id: int, borrower_name: str):
    """Marks a book as borrowed.

    Returns:
        Tuple (DBBook | None, str | None): (book_object, error_message)
    """
    book_to_borrow = get_book_by_id(db_session, book_id)
    if not book_to_borrow:
        return None, "Book not found in database."
    if book_to_borrow.is_borrowed:
        return None, f"'{book_to_borrow.title}' is already borrowed by {book_to_borrow.borrower_name}."

    book_to_borrow.is_borrowed = True
    book_to_borrow.borrower_name = borrower_name
    book_to_borrow.due_date = date.today() + timedelta(weeks=2)
    db_session.commit()
    db_session.refresh(book_to_borrow)
    return book_to_borrow, None


def return_selected_book(db_session: Session, book_id: int):
    """Marks a book as returned.

    Returns:
        Tuple (DBBook | None, str | None): (book_object, error_message)
    """
    book_to_return = get_book_by_id(db_session, book_id)
    if not book_to_return:
        return None, "Book not found in database."
    if not book_to_return.is_borrowed:
        return None, f"'{book_to_return.title}' is not currently borrowed."

    book_to_return.is_borrowed = False
    book_to_return.borrower_name = None
    book_to_return.due_date = None
    db_session.commit()
    db_session.refresh(book_to_return)
    return book_to_return, None