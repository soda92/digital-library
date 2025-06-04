import sys

module = sys.argv[1]

if module == "gui":
    from .gui import main_gui

    main_gui()
