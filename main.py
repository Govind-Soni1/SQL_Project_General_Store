# ==============================================================
# General Store Management & Billing System
# Application Entry Point
# ==============================================================

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Ensure project root is on the path so imports work when running from any CWD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Initialize the database and launch the application."""
    # ---- Step 1: Initialize database ----
    try:
        from database.schema import initialize_database
        initialize_database()
    except Exception as e:
        # If Tk isn't up yet, fall back to console error
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Database Error",
                f"Failed to initialize the database.\n\n"
                f"Make sure MySQL is running and the credentials in config.py are correct.\n\n"
                f"Error: {e}"
            )
            root.destroy()
        except Exception:
            print(f"FATAL: Could not initialize database: {e}")
        sys.exit(1)

    # ---- Step 2: Create reports directory ----
    from config import REPORTS_DIR
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # ---- Step 3: Launch GUI ----
    root = tk.Tk()

    # Set icon and window properties
    root.option_add("*Font", "Segoe\\ UI 10")

    from screens.main_screen import MainScreen
    app = MainScreen(root)

    # Center on screen
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"+{x}+{y}")

    root.protocol("WM_DELETE_WINDOW", app._on_exit)
    root.mainloop()


if __name__ == "__main__":
    main()
