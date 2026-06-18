# ==============================================================
# Main Screen — Dashboard with sidebar navigation
# ==============================================================

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from config import THEME, STORE_NAME
from screens.widgets import InfoCard, StyledButton, StatusBar, apply_theme
from screens.sales_screen import SalesScreen
from screens.purchase_screen import PurchaseScreen
from screens.inventory_screen import InventoryScreen
from screens.reports_screen import ReportsScreen
from screens.customer_history_screen import CustomerHistoryScreen
from screens.supplier_history_screen import SupplierHistoryScreen
from services import report_service
from utils.backup import backup_database, restore_database


class MainScreen:

    def __init__(self, root):
        self.root = root
        self.root.title(f"{STORE_NAME} — Management System")
        self.root.geometry("1200x720")
        self.root.minsize(1000, 600)
        self.root.configure(bg=THEME["bg_dark"])

        apply_theme(self.root)

        self._active_nav = None
        self._screens = {}

        self._build_ui()
        self._navigate("dashboard")
        self._refresh_dashboard()

    def _build_ui(self):
        # ---- Top bar ----
        topbar = tk.Frame(self.root, bg=THEME["bg_dark"], height=50)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(topbar, text=f"  🏪  {STORE_NAME}",
                 font=("Segoe UI Semibold", 14),
                 fg=THEME["text_primary"], bg=THEME["bg_dark"]).pack(
            side="left", padx=10, pady=10)

        # Backup/Restore buttons in top bar
        StyledButton(topbar, text="💾 Backup", command=self._do_backup,
                     font_size=8, padx=8, pady=3,
                     bg_color=THEME["bg_card"],
                     hover_color=THEME["accent_hover"]).pack(
            side="right", padx=4, pady=10)
        StyledButton(topbar, text="📂 Restore", command=self._do_restore,
                     font_size=8, padx=8, pady=3,
                     bg_color=THEME["bg_card"],
                     hover_color=THEME["accent_hover"]).pack(
            side="right", padx=4, pady=10)

        # ---- Main body ----
        body = tk.Frame(self.root, bg=THEME["bg_dark"])
        body.pack(fill="both", expand=True)

        # ---- Sidebar ----
        sidebar = tk.Frame(body, bg=THEME["bg_dark"], width=180)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        nav_items = [
            ("🏠  Dashboard", "dashboard"),
            ("🧾  Sales / Billing", "sales"),
            ("📦  Purchase Entry", "purchase"),
            ("📋  Inventory", "inventory"),
            ("📊  Reports", "reports"),
            ("👤  Customer History", "customer"),
            ("🏭  Supplier History", "supplier"),
        ]

        self._nav_buttons = {}
        for text, key in nav_items:
            btn = tk.Button(
                sidebar, text=text, font=("Segoe UI", 10),
                fg=THEME["text_secondary"], bg=THEME["bg_dark"],
                activebackground=THEME["accent"],
                activeforeground=THEME["text_primary"],
                relief="flat", anchor="w", padx=14, pady=10,
                cursor="hand2", borderwidth=0,
                command=lambda k=key: self._navigate(k),
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(
                bg=THEME["bg_light"]) if b != self._nav_buttons.get(self._active_nav) else None)
            btn.bind("<Leave>", lambda e, b=btn: b.config(
                bg=THEME["bg_dark"]) if b != self._nav_buttons.get(self._active_nav) else None)
            self._nav_buttons[key] = btn

        # Exit
        tk.Frame(sidebar, bg=THEME["border"], height=1).pack(fill="x", pady=8, padx=14)
        exit_btn = tk.Button(
            sidebar, text="🚪  Exit", font=("Segoe UI", 10),
            fg=THEME["danger"], bg=THEME["bg_dark"],
            activebackground=THEME["danger"],
            activeforeground=THEME["text_primary"],
            relief="flat", anchor="w", padx=14, pady=10,
            cursor="hand2", borderwidth=0,
            command=self._on_exit,
        )
        exit_btn.pack(fill="x")

        # Separator
        tk.Frame(body, bg=THEME["border"], width=1).pack(side="left", fill="y")

        # ---- Content area ----
        self._content = tk.Frame(body, bg=THEME["bg_medium"])
        self._content.pack(side="left", fill="both", expand=True)

        # ---- Status bar ----
        self._status_bar = StatusBar(self.root)
        self._status_bar.pack(fill="x", side="bottom")

    def _navigate(self, key):
        # Update nav button styles
        if self._active_nav and self._active_nav in self._nav_buttons:
            self._nav_buttons[self._active_nav].config(
                bg=THEME["bg_dark"], fg=THEME["text_secondary"]
            )

        if key in self._nav_buttons:
            self._nav_buttons[key].config(
                bg=THEME["accent"], fg=THEME["text_primary"]
            )

        self._active_nav = key

        # Clear content
        for widget in self._content.winfo_children():
            widget.destroy()

        # Create the screen
        if key == "dashboard":
            self._build_dashboard()
        elif key == "sales":
            screen = SalesScreen(self._content, status_bar=self._status_bar)
            screen.pack(fill="both", expand=True)
        elif key == "purchase":
            screen = PurchaseScreen(self._content, status_bar=self._status_bar)
            screen.pack(fill="both", expand=True)
        elif key == "inventory":
            screen = InventoryScreen(self._content, status_bar=self._status_bar)
            screen.pack(fill="both", expand=True)
        elif key == "reports":
            screen = ReportsScreen(self._content, status_bar=self._status_bar)
            screen.pack(fill="both", expand=True)
        elif key == "customer":
            screen = CustomerHistoryScreen(self._content, status_bar=self._status_bar)
            screen.pack(fill="both", expand=True)
        elif key == "supplier":
            screen = SupplierHistoryScreen(self._content, status_bar=self._status_bar)
            screen.pack(fill="both", expand=True)

    def _build_dashboard(self):
        container = tk.Frame(self._content, bg=THEME["bg_medium"])
        container.pack(fill="both", expand=True, padx=20, pady=16)

        tk.Label(container, text="📊  Dashboard",
                 font=("Segoe UI Semibold", 18),
                 fg=THEME["text_primary"], bg=THEME["bg_medium"]).pack(
            anchor="w", pady=(0, 16))

        # Cards row
        cards_frame = tk.Frame(container, bg=THEME["bg_medium"])
        cards_frame.pack(fill="x", pady=(0, 16))

        self._card_sales = InfoCard(cards_frame, "Today's Sales", "₹ 0.00",
                                     accent_color=THEME["success"])
        self._card_sales.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._card_bills = InfoCard(cards_frame, "Today's Bills", "0",
                                     accent_color=THEME["info"])
        self._card_bills.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._card_low = InfoCard(cards_frame, "Low Stock Items", "0",
                                   accent_color=THEME["warning"])
        self._card_low.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._card_products = InfoCard(cards_frame, "Total Products", "0",
                                        accent_color=THEME["accent"])
        self._card_products.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._card_dues = InfoCard(cards_frame, "Outstanding Dues", "₹ 0.00",
                                    accent_color=THEME["danger"])
        self._card_dues.pack(side="left", fill="x", expand=True)

        # Quick actions
        actions_frame = tk.LabelFrame(container, text="  Quick Actions  ",
                                       font=("Segoe UI Semibold", 10),
                                       fg=THEME["text_primary"],
                                       bg=THEME["bg_card"], bd=1, relief="groove")
        actions_frame.pack(fill="x", pady=(0, 16))

        inner = tk.Frame(actions_frame, bg=THEME["bg_card"])
        inner.pack(fill="x", padx=14, pady=14)

        quick_btns = [
            ("🧾 New Sale", lambda: self._navigate("sales"), THEME["success"]),
            ("📦 New Purchase", lambda: self._navigate("purchase"), THEME["info"]),
            ("📋 View Inventory", lambda: self._navigate("inventory"), THEME["accent"]),
            ("📊 View Reports", lambda: self._navigate("reports"), THEME["highlight"]),
            ("👤 Customer History", lambda: self._navigate("customer"), THEME["primary"]),
        ]

        for text, cmd, color in quick_btns:
            StyledButton(inner, text=text, command=cmd,
                         bg_color=color, hover_color=THEME["accent_hover"],
                         font_size=10, padx=18, pady=10).pack(
                side="left", padx=(0, 8))

        # Refresh button
        StyledButton(container, text="🔄 Refresh Dashboard",
                     command=self._refresh_dashboard,
                     font_size=9, padx=12, pady=4).pack(anchor="w")

    def _refresh_dashboard(self):
        try:
            data = report_service.get_dashboard_summary()
            if hasattr(self, "_card_sales"):
                self._card_sales.set_value(f"₹ {data['today_sales']:,.2f}")
                self._card_bills.set_value(str(data["today_bills"]))
                self._card_low.set_value(str(data["low_stock_count"]))
                self._card_products.set_value(str(data["total_products"]))
                self._card_dues.set_value(f"₹ {data['outstanding_dues']:,.2f}")
        except Exception:
            pass  # Dashboard loads even if DB is empty

    def _do_backup(self):
        result = backup_database()
        if result.startswith("Error") or result.startswith("Backup failed"):
            messagebox.showerror("Backup Failed", result)
        else:
            messagebox.showinfo("Backup", f"Database backed up to:\n{result}")
            self._status_bar.success(f"Backup saved: {result}")

    def _do_restore(self):
        filepath = filedialog.askopenfilename(
            title="Select Backup File",
            filetypes=[("SQL Files", "*.sql"), ("All Files", "*.*")],
        )
        if not filepath:
            return
        confirm = messagebox.askyesno(
            "Confirm Restore",
            f"This will replace ALL current data with the backup.\n\n"
            f"File: {filepath}\n\nContinue?"
        )
        if not confirm:
            return
        ok, msg = restore_database(filepath)
        if ok:
            messagebox.showinfo("Restore", msg)
            self._status_bar.success("Database restored successfully")
        else:
            messagebox.showerror("Restore Failed", msg)

    def _on_exit(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.root.destroy()
