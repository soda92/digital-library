import sys

module = sys.argv[1]

if module == "gui":
    from ..digital_library_gui.gui import main_gui

    main_gui()
