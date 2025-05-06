import tkinter as tk
# Import the AppWindow class FROM the gui module INSIDE the src package
from src import gui
# Keep sys for potential future use (like resource_path if needed differently)
import sys


def main():
    """Initializes Tkinter and runs the main application window."""
    print("Starting application...")  # Good for console debugging
    root = tk.Tk()
    app_window = gui.AppWindow(root)  # Create instance from the imported class
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application closed by user.")
    print("Application finished.")


if __name__ == "__main__":
    main()
