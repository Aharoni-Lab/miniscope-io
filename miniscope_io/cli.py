"""
CLI entry points
"""

from miniscope_io.commands.entry_points import main, main_functions

if __name__ == "__main__":
    import sys

    command = sys.argv[1] if len(sys.argv) > 1 else None
    if command in main_functions:
        main_functions[command]()
    else:
        main()
