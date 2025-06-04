import sys
from PySide6 import QtWidgets, QtCore

from digital_library.database import SessionLocal, create_db_tables
from .ui_setup import setup_main_window_ui
from .dialogs import prompt_edit_book_details, prompt_borrower_name
from .book_operations import (get_all_books, get_book_by_id, add_new_book,
                              update_existing_book, delete_existing_book,
                              borrow_selected_book, return_selected_book)

# Ensure database tables are created when the app starts
create_db_tables()


class LibraryApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_session = SessionLocal()

        # Setup UI using the dedicated function
        setup_main_window_ui(self)

        # Connect signals to slots
        self.connect_signals()

        self.load_books()
        self.update_button_states()  # Initial state

    def connect_signals(self):
        self.add_button.clicked.connect(self.add_book)
        self.edit_button.clicked.connect(self.edit_book)
        self.delete_button.clicked.connect(self.delete_book)
        self.borrow_button.clicked.connect(self.borrow_book)
        self.return_button.clicked.connect(self.return_book)
        self.refresh_button.clicked.connect(self.load_books)
        self.book_list_widget.itemDoubleClicked.connect(
            self.edit_book_dialog
        )  # Edit on double click
        self.book_list_widget.currentItemChanged.connect(self.update_button_states)

    def load_books(self):
        self.book_list_widget.clear()
        books = get_all_books(self.db_session)
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
            QtWidgets.QMessageBox.warning(
                self, "Input Error", "Title, Author, and ISBN fields must be filled."
            )
            return

        book, error = add_new_book(self.db_session, title, author, isbn)
        if error:
            QtWidgets.QMessageBox.warning(self, "Input Error", error)
        else:
            self.load_books()
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
        book_to_edit = get_book_by_id(self.db_session, book_id)

        if not book_to_edit:
            QtWidgets.QMessageBox.critical(self, "Error", "Book not found in database.")
            self.load_books()  # Refresh list in case of inconsistency
            return

        new_details = prompt_edit_book_details(self, book_to_edit.title, book_to_edit.author, book_to_edit.isbn)
        if not new_details:
            return # User cancelled

        new_title, new_author, new_isbn = new_details

        if not new_title or not new_author or not new_isbn:
            QtWidgets.QMessageBox.warning(
                self, "Input Error", "All fields must be filled for editing."
            )
            return

        updated_book, error = update_existing_book(self.db_session, book_id, new_title, new_author, new_isbn)

        if error:
            QtWidgets.QMessageBox.warning(self, "Update Error", error)
        else:
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
            success, error = delete_existing_book(self.db_session, book_id)
            if error:
                QtWidgets.QMessageBox.critical(self, "Error", error)
                self.load_books() # Refresh list
            else:
                self.load_books()
                QtWidgets.QMessageBox.information(self, "Success", "Book deleted successfully.")

    def clear_input_fields(self):
        self.title_input.clear()
        self.author_input.clear()
        self.isbn_input.clear()

    def borrow_book(self):
        current_item = self.book_list_widget.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.warning(
                self, "Selection Error", "Please select a book to borrow."
            )
            return

        book_id = current_item.data(QtCore.Qt.UserRole)
        # Check if book is already borrowed before prompting for name
        book = get_book_by_id(self.db_session, book_id)
        if not book:
             QtWidgets.QMessageBox.critical(self, "Error", "Book not found in database.")
             self.load_books()
             return
        if book.is_borrowed:
            QtWidgets.QMessageBox.information(self, "Book Unavailable", f"'{book.title}' is already borrowed by {book.borrower_name}.")
            return

        borrower_name = prompt_borrower_name(self)
        if borrower_name:
            borrowed_book, error = borrow_selected_book(self.db_session, book_id, borrower_name)
            if error:
                QtWidgets.QMessageBox.warning(self, "Borrow Error", error)
            else:
                self.load_books()
                QtWidgets.QMessageBox.information(self, "Success", f"Book '{borrowed_book.title}' borrowed by {borrower_name}.")
        elif borrower_name is not None: # User pressed OK but entered empty name
            QtWidgets.QMessageBox.warning(
                self, "Input Error", "Borrower's name cannot be empty."
            )

    def return_book(self):
        current_item = self.book_list_widget.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.warning(
                self, "Selection Error", "Please select a book to return."
            )
            return

        book_id = current_item.data(QtCore.Qt.UserRole)
        book_to_return = get_book_by_id(self.db_session, book_id)
        if not book_to_return:
            QtWidgets.QMessageBox.critical(self, "Error", "Book not found in database.")
            self.load_books()
            return
        if not book_to_return.is_borrowed:
            QtWidgets.QMessageBox.information(self, "Book Not Borrowed", f"'{book_to_return.title}' is not currently borrowed.")
            return

        reply = QtWidgets.QMessageBox.question(
            self, "Confirm Return", f"Return '{book_to_return.title}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            returned_book, error = return_selected_book(self.db_session, book_id)
            if error: QtWidgets.QMessageBox.warning(self, "Return Error", error)
            else: self.load_books(); QtWidgets.QMessageBox.information(self, "Success", f"Book '{returned_book.title}' returned.")

    def update_button_states(self):
        current_item = self.book_list_widget.currentItem()
        book_selected = current_item is not None

        self.edit_button.setEnabled(book_selected)
        self.delete_button.setEnabled(book_selected)

        if book_selected:
            book_id = current_item.data(QtCore.Qt.UserRole)
            book = get_book_by_id(self.db_session, book_id)
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
