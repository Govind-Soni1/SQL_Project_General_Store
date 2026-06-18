# ==============================================================
# Reusable Custom Tkinter Widgets
# ==============================================================

import tkinter as tk
from tkinter import ttk
from config import THEME


class InfoCard(tk.Frame):
    """A dashboard summary card with title, value, and optional icon color."""

    def __init__(self, parent, title, value="0", accent_color=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg=THEME["bg_card"], highlightbackground=THEME["border"],
                       highlightthickness=1, padx=18, pady=14)

        color = accent_color or THEME["primary"]

        # Accent bar on the left
        bar = tk.Frame(self, bg=color, width=4)
        bar.pack(side="left", fill="y", padx=(0, 12))

        text_frame = tk.Frame(self, bg=THEME["bg_card"])
        text_frame.pack(side="left", fill="both", expand=True)

        self._title_label = tk.Label(
            text_frame, text=title, font=("Segoe UI", 9),
            fg=THEME["text_secondary"], bg=THEME["bg_card"], anchor="w",
        )
        self._title_label.pack(fill="x")

        self._value_label = tk.Label(
            text_frame, text=str(value), font=("Segoe UI Semibold", 18),
            fg=THEME["text_primary"], bg=THEME["bg_card"], anchor="w",
        )
        self._value_label.pack(fill="x")

    def set_value(self, value):
        self._value_label.config(text=str(value))


class StyledButton(tk.Button):
    """A flat, modern-looking button with hover effects."""

    def __init__(self, parent, text="", bg_color=None, fg_color=None,
                 hover_color=None, font_size=10, padx=16, pady=8, **kwargs):
        bg = bg_color or THEME["button_bg"]
        fg = fg_color or THEME["button_fg"]
        hv = hover_color or THEME["accent_hover"]

        super().__init__(
            parent, text=text, font=("Segoe UI Semibold", font_size),
            bg=bg, fg=fg, activebackground=hv, activeforeground=fg,
            relief="flat", cursor="hand2", padx=padx, pady=pady,
            borderwidth=0, **kwargs,
        )
        self._bg = bg
        self._hv = hv
        self.bind("<Enter>", lambda e: self.config(bg=self._hv))
        self.bind("<Leave>", lambda e: self.config(bg=self._bg))


class StatusBar(tk.Frame):
    """A bottom status bar that shows transient messages."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=THEME["bg_dark"], **kwargs)
        self._label = tk.Label(
            self, text="Ready", font=("Segoe UI", 9),
            fg=THEME["text_muted"], bg=THEME["bg_dark"], anchor="w", padx=10,
        )
        self._label.pack(fill="x", pady=2)
        self._after_id = None

    def set_message(self, text, color=None, duration=5000):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._label.config(
            text=text, fg=color or THEME["text_primary"]
        )
        if duration:
            self._after_id = self.after(
                duration, lambda: self._label.config(
                    text="Ready", fg=THEME["text_muted"]
                )
            )

    def success(self, text, duration=5000):
        self.set_message(f"✓ {text}", THEME["success"], duration)

    def error(self, text, duration=8000):
        self.set_message(f"✗ {text}", THEME["danger"], duration)

    def info(self, text, duration=5000):
        self.set_message(f"ℹ {text}", THEME["info"], duration)


class SearchEntry(tk.Frame):
    """A search entry with a placeholder and clear button."""

    def __init__(self, parent, placeholder="Search...", on_search=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_medium"], **kwargs)
        self._placeholder = placeholder
        self._on_search = on_search

        self._entry = tk.Entry(
            self, font=("Segoe UI", 11), bg=THEME["entry_bg"],
            fg=THEME["text_muted"], insertbackground=THEME["text_primary"],
            relief="flat", borderwidth=0,
        )
        self._entry.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=6)
        self._entry.insert(0, placeholder)

        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<Return>", self._do_search)
        self._entry.bind("<KeyRelease>", self._do_search)

        self._clear_btn = tk.Label(
            self, text="✕", font=("Segoe UI", 10), fg=THEME["text_muted"],
            bg=THEME["entry_bg"], cursor="hand2", padx=8,
        )
        self._clear_btn.pack(side="right", pady=6)
        self._clear_btn.bind("<Button-1>", self._clear)

        self.configure(highlightbackground=THEME["border"], highlightthickness=1)

    def _on_focus_in(self, event):
        if self._entry.get() == self._placeholder:
            self._entry.delete(0, "end")
            self._entry.config(fg=THEME["entry_fg"])

    def _on_focus_out(self, event):
        if not self._entry.get():
            self._entry.insert(0, self._placeholder)
            self._entry.config(fg=THEME["text_muted"])

    def _do_search(self, event=None):
        text = self._entry.get()
        if text == self._placeholder:
            text = ""
        if self._on_search:
            self._on_search(text)

    def _clear(self, event=None):
        self._entry.delete(0, "end")
        self._entry.config(fg=THEME["text_muted"])
        self._entry.insert(0, self._placeholder)
        if self._on_search:
            self._on_search("")

    def get_text(self):
        text = self._entry.get()
        return "" if text == self._placeholder else text


class StyledTreeview(ttk.Treeview):
    """Treeview with alternating row colors and custom styling."""

    def __init__(self, parent, columns, show="headings", **kwargs):
        super().__init__(parent, columns=columns, show=show, **kwargs)

        # Scrollbar
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.yview)
        self.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        self.tag_configure("odd", background=THEME["treeview_odd"])
        self.tag_configure("even", background=THEME["treeview_even"])
        self.tag_configure("low_stock", background="#3d1a1a",
                           foreground=THEME["danger"])

    def insert_rows(self, data, key_map=None, low_stock_check=None):
        """Clear and insert rows with alternating colors.

        Parameters
        ----------
        data : list[dict]
        key_map : list[str]  keys to extract from each dict, in column order
        low_stock_check : callable(row_dict) -> bool  for highlighting
        """
        self.delete(*self.get_children())
        for i, row in enumerate(data):
            if key_map:
                values = [row.get(k, "") for k in key_map]
            else:
                values = list(row.values())

            tag = "odd" if i % 2 == 0 else "even"
            if low_stock_check and low_stock_check(row):
                tag = "low_stock"

            self.insert("", "end", values=values, tags=(tag,))


def apply_theme(root):
    """Apply the dark theme to the root window and ttk styles."""
    style = ttk.Style(root)
    style.theme_use("clam")

    # General
    style.configure(".", background=THEME["bg_medium"],
                     foreground=THEME["text_primary"],
                     fieldbackground=THEME["entry_bg"],
                     font=("Segoe UI", 10))

    # Treeview
    style.configure("Treeview",
                     background=THEME["bg_medium"],
                     foreground=THEME["text_primary"],
                     fieldbackground=THEME["bg_medium"],
                     borderwidth=0,
                     rowheight=28,
                     font=("Segoe UI", 10))
    style.configure("Treeview.Heading",
                     background=THEME["accent"],
                     foreground=THEME["text_primary"],
                     font=("Segoe UI Semibold", 10),
                     borderwidth=0)
    style.map("Treeview.Heading",
              background=[("active", THEME["accent_hover"])])
    style.map("Treeview",
              background=[("selected", THEME["highlight"])],
              foreground=[("selected", THEME["text_primary"])])

    # Notebook (tabs)
    style.configure("TNotebook", background=THEME["bg_dark"], borderwidth=0)
    style.configure("TNotebook.Tab",
                     background=THEME["bg_card"],
                     foreground=THEME["text_secondary"],
                     padding=[14, 6],
                     font=("Segoe UI Semibold", 10))
    style.map("TNotebook.Tab",
              background=[("selected", THEME["accent"])],
              foreground=[("selected", THEME["text_primary"])])

    # Entry
    style.configure("TEntry",
                     fieldbackground=THEME["entry_bg"],
                     foreground=THEME["entry_fg"],
                     borderwidth=1,
                     relief="flat")

    # Combobox
    style.configure("TCombobox",
                     fieldbackground=THEME["entry_bg"],
                     foreground=THEME["entry_fg"],
                     selectbackground=THEME["accent"],
                     selectforeground=THEME["text_primary"])
    style.map("TCombobox",
              fieldbackground=[("readonly", THEME["entry_bg"])])

    # Scrollbar
    style.configure("Vertical.TScrollbar",
                     background=THEME["bg_card"],
                     troughcolor=THEME["bg_dark"],
                     borderwidth=0)

    # LabelFrame
    style.configure("TLabelframe",
                     background=THEME["bg_medium"],
                     foreground=THEME["text_primary"])
    style.configure("TLabelframe.Label",
                     background=THEME["bg_medium"],
                     foreground=THEME["text_primary"],
                     font=("Segoe UI Semibold", 10))

    # Radiobutton
    style.configure("TRadiobutton",
                     background=THEME["bg_medium"],
                     foreground=THEME["text_primary"],
                     font=("Segoe UI", 10))

    # Checkbutton
    style.configure("TCheckbutton",
                     background=THEME["bg_medium"],
                     foreground=THEME["text_primary"],
                     font=("Segoe UI", 10))
