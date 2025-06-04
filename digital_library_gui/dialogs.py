from PySide6 import QtWidgets


def prompt_edit_book_details(parent, current_title, current_author, current_isbn):
    """
    Prompts the user for new book details using QInputDialog.

    Args:
        parent: The parent widget for the dialogs.
        current_title: The current title of the book.
        current_author: The current author of the book.
        current_isbn: The current ISBN of the book.

    Returns:
        A tuple (title, author, isbn) if all inputs are 'ok' and valid,
        otherwise None.
    """
    title, ok1 = QtWidgets.QInputDialog.getText(
        parent, "Edit Book", "Enter new title:", QtWidgets.QLineEdit.Normal, current_title
    )
    if not ok1:
        return None

    author, ok2 = QtWidgets.QInputDialog.getText(
        parent, "Edit Book", "Enter new author:", QtWidgets.QLineEdit.Normal, current_author
    )
    if not ok2:
        return None

    isbn, ok3 = QtWidgets.QInputDialog.getText(
        parent, "Edit Book", "Enter new ISBN:", QtWidgets.QLineEdit.Normal, current_isbn
    )
    if not ok3:
        return None

    return title.strip(), author.strip(), isbn.strip()

def prompt_borrower_name(parent):
    """Prompts the user for the borrower's name."""
    borrower_name, ok = QtWidgets.QInputDialog.getText(parent, "Borrow Book", "Enter borrower's name:")
    return borrower_name.strip() if ok and borrower_name.strip() else None