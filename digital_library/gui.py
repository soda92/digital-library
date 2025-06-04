import sys
from PySide6 import QtWidgets, QtCore

# Import specific classes from QtWidgets and QtCore using the module names

from datetime import timedelta, date
from .database import SessionLocal, Book as DBBook, create_db_tables

# Ensure database tables are created when the app starts
create_db_tables()


class LibraryApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Digital Library")
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        # Use QtWidgets.QVBoxLayout
        self.layout = QtWidgets.QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.db_session = SessionLocal()

        self.setup_ui()

    def setup_ui(self):
        # Input fields
        input_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(input_layout)

        self.title_label = QtWidgets.QLabel("Title:")
        self.title_input = QtWidgets.QLineEdit()
        input_layout.addWidget(self.title_label)
        input_layout.addWidget(self.title_input)

        self.author_label = QtWidgets.QLabel("Author:")
        self.author_input = QtWidgets.QLineEdit()
        input_layout.addWidget(self.author_label)
        input_layout.addWidget(self.author_input)

        self.isbn_label = QtWidgets.QLabel("ISBN:")
        self.isbn_input = QtWidgets.QLineEdit()
        input_layout.addWidget(self.isbn_label)
        input_layout.addWidget(self.isbn_input)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(button_layout)

        self.add_button = QtWidgets.QPushButton("Add Book")
        self.add_button.clicked.connect(self.add_book)
        button_layout.addWidget(self.add_button)

        self.edit_button = QtWidgets.QPushButton("Edit Book")
        self.edit_button.clicked.connect(self.edit_book)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QtWidgets.QPushButton("Delete Book")
        self.delete_button.clicked.connect(self.delete_book)
        button_layout.addWidget(self.delete_button)

        self.borrow_button = QtWidgets.QPushButton("Borrow Book")
        self.borrow_button.clicked.connect(self.borrow_book)
        button_layout.addWidget(self.borrow_button)

        self.return_button = QtWidgets.QPushButton("Return Book")
        self.return_button.clicked.connect(self.return_book)
        button_layout.addWidget(self.return_button)

        self.refresh_button = QtWidgets.QPushButton("Refresh List")
        self.refresh_button.clicked.connect(self.load_books) # Connect to existing load_books
        button_layout.addWidget(self.refresh_button)

        # Book list
        self.book_list_widget = QtWidgets.QListWidget()
        self.book_list_widget.itemDoubleClicked.connect(
            self.edit_book_dialog
        )  # Edit on double click
        self.book_list_widget.currentItemChanged.connect(self.update_button_states)
        self.layout.addWidget(self.book_list_widget)

        self.load_books()
        self.update_button_states() # Initial state

    def load_books(self):
        self.book_list_widget.clear()
        books = self.db_session.query(DBBook).all()
        for book in books:
            item = QtWidgets.QListWidgetItem(str(book))
            item.setData(QtCore.Qt.UserRole, book.id)  # Store book ID with the item
            self.book_list_widget.addItem(item)
        self.update_button_states()

    def add_book(self):
        title = self.title_input.text().strip()
        author = self.author_input.text().strip()
        isbn = self.isbn_input.text().strip()

        if not title or not author or not isbn:
            QtWidgets.QMessageBox.warning(self, "Input Error", "All fields must be filled.")
            return

        # Check if ISBN already exists
        existing_book = (
            self.db_session.query(DBBook).filter(DBBook.isbn == isbn).first()
        )
        if existing_book:
            QtWidgets.QMessageBox.warning(
                self, "Input Error", f"Book with ISBN {isbn} already exists."
            )
            return

        new_book = DBBook(title=title, author=author, isbn=isbn)
        self.db_session.add(new_book)
        self.db_session.commit()
        self.db_session.refresh(new_book)  # Get the ID

        self.load_books()  # Refresh the list
        self.clear_input_fields()
        QtWidgets.QMessageBox.information(self, "Success", "Book added successfully.")

    def edit_book_dialog(self, item=None):
        if not item:  # Called from button click
            current_item = self.book_list_widget.currentItem()
        else:  # Called from double click
            current_item = item

        if not current_item:
            QtWidgets.QMessageBox.warning(
                self, "Selection Error", "Please select a book to edit."
            )
            return

        book_id = current_item.data(QtCore.Qt.UserRole)
        book_to_edit = (
            self.db_session.query(DBBook).filter(DBBook.id == book_id).first()
        )

        if not book_to_edit:
            QtWidgets.QMessageBox.critical(self, "Error", "Book not found in database.")
            self.load_books()  # Refresh list in case of inconsistency
            return

        title, ok1 = QtWidgets.QInputDialog.getText(
            self, "Edit Book", "Enter new title:", QtWidgets.QLineEdit.Normal, book_to_edit.title
        )
        if not ok1:
            return
        author, ok2 = QtWidgets.QInputDialog.getText(
            self,
            "Edit Book",
            "Enter new author:",
            QtWidgets.QLineEdit.Normal,
            book_to_edit.author,
        )
        if not ok2:
            return
        # ISBN is usually not editable, but for this demo, we'll allow it.
        # In a real app, you might want to prevent ISBN changes or handle them carefully due to uniqueness.
        isbn, ok3 = QtWidgets.QInputDialog.getText(
            self, "Edit Book", "Enter new ISBN:", QtWidgets.QLineEdit.Normal, book_to_edit.isbn
        )
        if not ok3:
            return

        if not title.strip() or not author.strip() or not isbn.strip():
            QtWidgets.QMessageBox.warning(
                self, "Input Error", "All fields must be filled for editing."
            )
            return

        # Check if new ISBN conflicts with another book (excluding itself)
        existing_book = (
            self.db_session.query(DBBook)
            .filter(DBBook.isbn == isbn.strip(), DBBook.id != book_id)
            .first()
        )
        if existing_book:
            QtWidgets.QMessageBox.warning(
                self,
                "Input Error",
                f"Another book with ISBN {isbn.strip()} already exists.",
            )
            return

        book_to_edit.title = title.strip()
        book_to_edit.author = author.strip()
        book_to_edit.isbn = isbn.strip()
        self.db_session.commit()
        self.load_books()
        QtWidgets.QMessageBox.information(self, "Success", "Book updated successfully.")

    def edit_book(self):  # Wrapper for button click
        self.edit_book_dialog()

    def delete_book(self):
        current_item = self.book_list_widget.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.warning(
                self, "Selection Error", "Please select a book to delete."
            )
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{current_item.text()}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes:
            book_id = current_item.data(QtCore.Qt.UserRole)
            book_to_delete = (
                self.db_session.query(DBBook).filter(DBBook.id == book_id).first()
            )
            if book_to_delete:
                self.db_session.delete(book_to_delete)
                self.db_session.commit()
                self.load_books()
                QtWidgets.QMessageBox.information(self, "Success", "Book deleted successfully.")
            else:
                QtWidgets.QMessageBox.critical(
                    self, "Error", "Book not found in database for deletion."
                )
                self.load_books()  # Refresh list

    def clear_input_fields(self):
        self.title_input.clear()
        self.author_input.clear()
        self.isbn_input.clear()

    def borrow_book(self):
        current_item = self.book_list_widget.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.warning(self, "Selection Error", "Please select a book to borrow.")
            return

        book_id = current_item.data(QtCore.Qt.UserRole)
        book_to_borrow = self.db_session.query(DBBook).filter(DBBook.id == book_id).first()

        if not book_to_borrow:
            QtWidgets.QMessageBox.critical(self, "Error", "Book not found in database.")
            self.load_books()
            return

        if book_to_borrow.is_borrowed:
            QtWidgets.QMessageBox.information(self, "Book Unavailable", f"'{book_to_borrow.title}' is already borrowed by {book_to_borrow.borrower_name}.")
            return

        borrower_name, ok = QtWidgets.QInputDialog.getText(self, "Borrow Book", "Enter borrower's name:")
        if ok and borrower_name.strip():
            book_to_borrow.is_borrowed = True
            book_to_borrow.borrower_name = borrower_name.strip()
            # Set due date, e.g., 2 weeks from today
            book_to_borrow.due_date = date.today() + timedelta(weeks=2)
            
            self.db_session.commit()
            self.load_books()
            QtWidgets.QMessageBox.information(self, "Success", f"Book '{book_to_borrow.title}' borrowed by {borrower_name.strip()}.")
        elif ok and not borrower_name.strip():
            QtWidgets.QMessageBox.warning(self, "Input Error", "Borrower's name cannot be empty.")

    def return_book(self):
        current_item = self.book_list_widget.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.warning(self, "Selection Error", "Please select a book to return.")
            return

        book_id = current_item.data(QtCore.Qt.UserRole)
        book_to_return = self.db_session.query(DBBook).filter(DBBook.id == book_id).first()

        if not book_to_return:
            QtWidgets.QMessageBox.critical(self, "Error", "Book not found in database.")
            self.load_books()
            return

        if not book_to_return.is_borrowed:
            QtWidgets.QMessageBox.information(self, "Book Not Borrowed", f"'{book_to_return.title}' is not currently borrowed.")
            return

        reply = QtWidgets.QMessageBox.question(self, "Confirm Return",
                                     f"Are you sure you want to return '{book_to_return.title}' "
                                     f"(borrowed by {book_to_return.borrower_name})?",
                                     QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        
        if reply == QtWidgets.QMessageBox.Yes:
            book_to_return.is_borrowed = False
            book_to_return.borrower_name = None
            book_to_return.due_date = None
            self.db_session.commit()
            self.load_books()
            QtWidgets.QMessageBox.information(self, "Success", f"Book '{book_to_return.title}' returned successfully.")

    def update_button_states(self):
        current_item = self.book_list_widget.currentItem()
        book_selected = current_item is not None
        
        self.edit_button.setEnabled(book_selected)
        self.delete_button.setEnabled(book_selected)

        if book_selected:
            book_id = current_item.data(QtCore.Qt.UserRole)
            book = self.db_session.query(DBBook).filter(DBBook.id == book_id).first()
            if book:
                self.borrow_button.setEnabled(not book.is_borrowed)
                self.return_button.setEnabled(book.is_borrowed)
                return
        
        self.borrow_button.setEnabled(False)
        self.return_button.setEnabled(False)

    def closeEvent(self, event):
        self.db_session.close()
        super().closeEvent(event)


def main_gui():
    app = QtWidgets.QApplication(sys.argv)
    window = LibraryApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main_gui()
