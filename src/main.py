import tkinter as tk
import gui
import sys  # For package hooks or sys.exit


def run_app():
    """Initializes Tkinter and runs the main application window."""
    # 1. Creates the main Tkinter window object
    root = tk.Tk()

    # 2. Creates application window instance, passing the root window
    app_window = gui.AppWindow(root)

    # 3. Starts the Tkinter event loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application closed by user.")


if __name__ == "__main__":
    # This ensures the code runs only when the script is executed directly
    print("Starting application...")  # Message to show it's starting
    run_app()
    print("Application finished.")  # Message when window closes
