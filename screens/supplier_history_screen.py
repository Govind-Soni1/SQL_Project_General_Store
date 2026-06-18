# ==============================================================
# Supplier History Screen — view purchases per supplier
# ==============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME
from screens.widgets import StyledButton
from services import supplier_service
from utils.validators import validate_phone


class SupplierHistoryScreen(tk.Frame):

    def __init__(self, parent, status_bar=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_medium"], **kwargs)
        self.status_bar = status_bar
        self._supplier = None
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="🏭  Supplier History", font=("Segoe UI Semibold", 16),
                 fg=THEME["text_primary"], bg=THEME["bg_medium"]).pack(
            anchor="w", padx=20, pady=(16, 6))

        # Search
        search_frame = tk.Frame(self, bg=THEME["bg_medium"])
        search_frame.pack(fill="x", padx=20, pady=(0, 8))

        tk.Label(search_frame, text="Phone:", font=("Segoe UI", 10),
                 fg=THEME["text_secondary"], bg=THEME["bg_medium"]).pack(side="left")
        self._phone_entry = tk.Entry(search_frame, font=("Segoe UI", 11),
                                      bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                      insertbackground=THEME["text_primary"],
                                      relief="flat", width=16)
        self._phone_entry.pack(side="left", padx=(6, 8))
        StyledButton(search_frame, text="🔍 Find", command=self._find_supplier,
                     font_size=9, padx=10, pady=4).pack(side="left")
        StyledButton(search_frame, text="📋 All Suppliers",
                     command=self._show_all_suppliers,
                     font_size=9, padx=10, pady=4).pack(side="left", padx=6)

        # Supplier info
        self._info_lbl = tk.Label(self, text="", font=("Segoe UI", 10),
                                   fg=THEME["text_secondary"], bg=THEME["bg_medium"],
                                   anchor="w")
        self._info_lbl.pack(fill="x", padx=20)

        self._summary_lbl = tk.Label(self, text="", font=("Segoe UI Semibold", 10),
                                      fg=THEME["info"], bg=THEME["bg_medium"],
                                      anchor="w")
        self._summary_lbl.pack(fill="x", padx=20, pady=(2, 6))

        # Treeview
        tree_frame = tk.Frame(self, bg=THEME["bg_medium"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        cols = ("pur_no", "date", "subtotal", "discount", "total", "notes")
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=14)
        for col, hd, w in [
            ("pur_no", "Purchase No", 130), ("date", "Date", 120),
            ("subtotal", "Subtotal", 100), ("discount", "Discount", 90),
            ("total", "Grand Total", 110), ("notes", "Notes", 140),
        ]:
            self._tree.heading(col, text=hd)
            self._tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree.tag_configure("odd", background=THEME["treeview_odd"])
        self._tree.tag_configure("even", background=THEME["treeview_even"])

    def _find_supplier(self):
        phone = self._phone_entry.get().strip()
        valid, result = validate_phone(phone)
        if not valid:
            messagebox.showwarning("Validation", result)
            return

        supplier = supplier_service.find_by_phone(result)
        if not supplier:
            self._info_lbl.config(text="Supplier not found.", fg=THEME["danger"])
            return

        self._supplier = supplier
        self._info_lbl.config(
            text=f"Supplier: {supplier['supplier_name']} | Phone: {supplier['phone']} | "
                 f"GST: {supplier.get('gst_number', 'N/A')}",
            fg=THEME["text_primary"],
        )
        self._load_history(supplier["supplier_id"])

    def _show_all_suppliers(self):
        suppliers = supplier_service.get_all_suppliers()
        self._tree.delete(*self._tree.get_children())
        self._info_lbl.config(text=f"All Suppliers ({len(suppliers)})",
                               fg=THEME["text_primary"])

        for col in self._tree["columns"]:
            self._tree.heading(col, text="")
        self._tree.heading("pur_no", text="ID")
        self._tree.heading("date", text="Name")
        self._tree.heading("subtotal", text="Phone")
        self._tree.heading("discount", text="GST No")
        self._tree.heading("total", text="Total Purchases")
        self._tree.heading("notes", text="")

        for i, s in enumerate(suppliers):
            total = supplier_service.get_supplier_purchase_total(s["supplier_id"])
            tag = "odd" if i % 2 == 0 else "even"
            self._tree.insert("", "end", values=(
                s["supplier_id"], s["supplier_name"], s["phone"],
                s.get("gst_number", ""), f"₹{total:,.2f}", "",
            ), tags=(tag,))

        self._summary_lbl.config(text="")

    def _load_history(self, supplier_id):
        purchases = supplier_service.get_supplier_purchases(supplier_id)
        total = supplier_service.get_supplier_purchase_total(supplier_id)

        # Reset headers
        for col, hd in [("pur_no", "Purchase No"), ("date", "Date"),
                         ("subtotal", "Subtotal"), ("discount", "Discount"),
                         ("total", "Grand Total"), ("notes", "Notes")]:
            self._tree.heading(col, text=hd)

        self._tree.delete(*self._tree.get_children())
        for i, p in enumerate(purchases):
            tag = "odd" if i % 2 == 0 else "even"
            self._tree.insert("", "end", values=(
                p["purchase_number"], str(p.get("purchase_date", "")),
                f"₹{float(p['subtotal']):,.2f}",
                f"₹{float(p['discount']):,.2f}",
                f"₹{float(p['grand_total']):,.2f}",
                p.get("notes", ""),
            ), tags=(tag,))

        self._summary_lbl.config(
            text=f"Total Purchases: {len(purchases)} | Total Amount: ₹{total:,.2f}"
        )
