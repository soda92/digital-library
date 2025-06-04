from PySide6 import QtWidgets


def setup_main_window_ui(main_window):
    """
    Sets up the UI elements for the main library application window.
    Widgets are created and assigned as attributes to main_window.
    """
    main_window.setWindowTitle("Digital Library")
    main_window.setGeometry(100, 100, 600, 400)

    main_window.central_widget = QtWidgets.QWidget()
    main_window.setCentralWidget(main_window.central_widget)
    main_window.layout = QtWidgets.QVBoxLayout()
    main_window.central_widget.setLayout(main_window.layout)

    # Input fields
    input_layout = QtWidgets.QHBoxLayout()
    main_window.layout.addLayout(input_layout)

    main_window.title_label = QtWidgets.QLabel("Title:")
    main_window.title_input = QtWidgets.QLineEdit()
    input_layout.addWidget(main_window.title_label)
    input_layout.addWidget(main_window.title_input)

    main_window.author_label = QtWidgets.QLabel("Author:")
    main_window.author_input = QtWidgets.QLineEdit()
    input_layout.addWidget(main_window.author_label)
    input_layout.addWidget(main_window.author_input)

    main_window.isbn_label = QtWidgets.QLabel("ISBN:")
    main_window.isbn_input = QtWidgets.QLineEdit()
    input_layout.addWidget(main_window.isbn_label)
    input_layout.addWidget(main_window.isbn_input)

    # Buttons
    button_layout = QtWidgets.QHBoxLayout()
    main_window.layout.addLayout(button_layout)

    main_window.add_button = QtWidgets.QPushButton("Add Book")
    main_window.edit_button = QtWidgets.QPushButton("Edit Book")
    main_window.delete_button = QtWidgets.QPushButton("Delete Book")
    main_window.borrow_button = QtWidgets.QPushButton("Borrow Book")
    main_window.return_button = QtWidgets.QPushButton("Return Book")
    main_window.refresh_button = QtWidgets.QPushButton("Refresh List")

    button_layout.addWidget(main_window.add_button)
    button_layout.addWidget(main_window.edit_button)
    button_layout.addWidget(main_window.delete_button)
    button_layout.addWidget(main_window.borrow_button)
    button_layout.addWidget(main_window.return_button)
    button_layout.addWidget(main_window.refresh_button)

    # Book list
    main_window.book_list_widget = QtWidgets.QListWidget()
    main_window.layout.addWidget(main_window.book_list_widget)