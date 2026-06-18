# ==============================================================
# Inventory Screen — Read-only view with search & low-stock filter
# ==============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME
from screens.widgets import StyledButton, SearchEntry
from services import inventory_service
from utils.excel_export import export_to_excel


class InventoryScreen(tk.Frame):

    def __init__(self, parent, status_bar=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_medium"], **kwargs)
        self.status_bar = status_bar
        self._low_stock_only = False
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # Title row
        top = tk.Frame(self, bg=THEME["bg_medium"])
        top.pack(fill="x", padx=20, pady=(16, 6))

        tk.Label(top, text="📋  Inventory", font=("Segoe UI Semibold", 16),
                 fg=THEME["text_primary"], bg=THEME["bg_medium"]).pack(side="left")

        StyledButton(top, text="📥 Export Excel", command=self._export_excel,
                     font_size=9, padx=12, pady=4).pack(side="right", padx=4)
        self._low_btn = StyledButton(
            top, text="⚠ Low Stock", command=self._toggle_low_stock,
            bg_color=THEME["warning"], hover_color="#ffbe33",
            font_size=9, padx=12, pady=4,
        )
        self._low_btn.pack(side="right", padx=4)
        StyledButton(top, text="🔄 Refresh", command=self._load_data,
                     font_size=9, padx=12, pady=4).pack(side="right", padx=4)

        # Search bar
        search_frame = tk.Frame(self, bg=THEME["bg_medium"])
        search_frame.pack(fill="x", padx=20, pady=(0, 8))
        self._search = SearchEntry(search_frame, placeholder="Search by name, ID, or barcode...",
                                    on_search=self._on_search)
        self._search.pack(fill="x")

        # Summary cards
        summary_frame = tk.Frame(self, bg=THEME["bg_medium"])
        summary_frame.pack(fill="x", padx=20, pady=(0, 8))

        self._total_products_lbl = tk.Label(
            summary_frame, text="Products: 0", font=("Segoe UI", 10),
            fg=THEME["text_secondary"], bg=THEME["bg_medium"],
        )
        self._total_products_lbl.pack(side="left", padx=(0, 20))
        self._total_items_lbl = tk.Label(
            summary_frame, text="Total Stock: 0", font=("Segoe UI", 10),
            fg=THEME["text_secondary"], bg=THEME["bg_medium"],
        )
        self._total_items_lbl.pack(side="left", padx=(0, 20))
        self._inventory_value_lbl = tk.Label(
            summary_frame, text="Value: ₹ 0", font=("Segoe UI", 10),
            fg=THEME["info"], bg=THEME["bg_medium"],
        )
        self._inventory_value_lbl.pack(side="left")

        # Treeview
        tree_frame = tk.Frame(self, bg=THEME["bg_medium"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        cols = ("id", "name", "category", "unit", "stock", "buy_price",
                "sell_price", "reorder")
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                   height=16)
        for col, hd, w, anchor in [
            ("id", "ID", 45, "center"),
            ("name", "Product Name", 200, "w"),
            ("category", "Category", 120, "w"),
            ("unit", "Unit", 55, "center"),
            ("stock", "Stock", 65, "center"),
            ("buy_price", "Buy Price", 90, "e"),
            ("sell_price", "Sell Price", 90, "e"),
            ("reorder", "Reorder Lvl", 80, "center"),
        ]:
            self._tree.heading(col, text=hd)
            self._tree.column(col, width=w, anchor=anchor,
                              stretch=col == "name")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree.tag_configure("odd", background=THEME["treeview_odd"])
        self._tree.tag_configure("even", background=THEME["treeview_even"])
        self._tree.tag_configure("low_stock", background="#3d1a1a",
                                  foreground=THEME["danger"])

    def _load_data(self, keyword=""):
        if self._low_stock_only:
            data = inventory_service.get_low_stock_products()
        elif keyword:
            data = inventory_service.search_product(keyword)
        else:
            data = inventory_service.get_all_products()

        self._tree.delete(*self._tree.get_children())
        for i, p in enumerate(data):
            stock = p.get("stock", 0)
            reorder = p.get("reorder_level", 10)
            tag = "low_stock" if stock <= reorder else ("odd" if i % 2 == 0 else "even")
            self._tree.insert("", "end", values=(
                p["product_id"], p["product_name"],
                p.get("category_name", "N/A"), p.get("unit", "Pcs"),
                stock,
                f"₹{float(p.get('purchase_price', 0)):,.2f}",
                f"₹{float(p.get('selling_price', 0)):,.2f}",
                reorder,
            ), tags=(tag,))

        # Update summary
        inv = inventory_service.get_inventory_value()
        if inv:
            self._total_products_lbl.config(text=f"Products: {inv['total_products']}")
            self._total_items_lbl.config(text=f"Total Stock: {inv['total_items']}")
            self._inventory_value_lbl.config(
                text=f"Value: ₹ {float(inv['total_value']):,.2f}"
            )

    def _on_search(self, keyword):
        self._low_stock_only = False
        self._low_btn.config(text="⚠ Low Stock")
        self._load_data(keyword)

    def _toggle_low_stock(self):
        self._low_stock_only = not self._low_stock_only
        if self._low_stock_only:
            self._low_btn.config(text="📋 Show All")
        else:
            self._low_btn.config(text="⚠ Low Stock")
        self._load_data()

    def _export_excel(self):
        data = inventory_service.get_all_products()
        columns = [
            ("product_id", "Product ID", 12),
            ("product_name", "Product Name", 30),
            ("category_name", "Category", 18),
            ("unit", "Unit", 10),
            ("stock", "Stock", 10),
            ("purchase_price", "Buy Price", 14),
            ("selling_price", "Sell Price", 14),
            ("reorder_level", "Reorder Level", 14),
        ]
        try:
            path = export_to_excel(data, columns, sheet_name="Inventory",
                                    title="Inventory Report")
            if self.status_bar:
                self.status_bar.success(f"Exported to {path}")
            messagebox.showinfo("Export", f"Inventory exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
