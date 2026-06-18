# ==============================================================
# Reports Screen — Dynamic report viewer with export
# ==============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from config import THEME
from screens.widgets import StyledButton, InfoCard
from services import report_service
from utils.excel_export import export_to_excel


class ReportsScreen(tk.Frame):

    def __init__(self, parent, status_bar=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_medium"], **kwargs)
        self.status_bar = status_bar
        self._current_data = []
        self._current_columns = []
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="📊  Reports", font=("Segoe UI Semibold", 16),
                 fg=THEME["text_primary"], bg=THEME["bg_medium"]).pack(
            anchor="w", padx=20, pady=(16, 6))

        # Top: Report buttons
        btn_frame = tk.Frame(self, bg=THEME["bg_medium"])
        btn_frame.pack(fill="x", padx=20, pady=(0, 8))

        reports = [
            ("Today's Sales", self._report_today_sales, THEME["success"]),
            ("Monthly Sales", self._report_monthly_sales, THEME["info"]),
            ("Yearly Sales", self._report_yearly_sales, THEME["accent"]),
            ("Inventory", self._report_inventory, THEME["button_bg"]),
            ("Low Stock", self._report_low_stock, THEME["warning"]),
            ("Best Selling", self._report_best_selling, THEME["highlight"]),
            ("Profit Report", self._report_profit, THEME["primary"]),
            ("Supplier Report", self._report_supplier, THEME["accent"]),
            ("Customer Report", self._report_customer, THEME["info"]),
            ("Outstanding Dues", self._report_dues, THEME["danger"]),
        ]

        for i, (text, cmd, color) in enumerate(reports):
            StyledButton(btn_frame, text=text, command=cmd,
                         bg_color=color, hover_color=THEME["accent_hover"],
                         font_size=9, padx=10, pady=5).grid(
                row=i // 5, column=i % 5, padx=3, pady=3, sticky="ew")
        for c in range(5):
            btn_frame.grid_columnconfigure(c, weight=1)

        # Date filter row
        filter_frame = tk.Frame(self, bg=THEME["bg_medium"])
        filter_frame.pack(fill="x", padx=20, pady=(0, 8))

        tk.Label(filter_frame, text="Year:", font=("Segoe UI", 9),
                 fg=THEME["text_secondary"], bg=THEME["bg_medium"]).pack(side="left")
        self._year_var = tk.StringVar(value=str(datetime.now().year))
        year_entry = tk.Entry(filter_frame, textvariable=self._year_var,
                               font=("Segoe UI", 10), bg=THEME["entry_bg"],
                               fg=THEME["entry_fg"],
                               insertbackground=THEME["text_primary"],
                               relief="flat", width=6)
        year_entry.pack(side="left", padx=(4, 12))

        tk.Label(filter_frame, text="Month:", font=("Segoe UI", 9),
                 fg=THEME["text_secondary"], bg=THEME["bg_medium"]).pack(side="left")
        self._month_var = tk.StringVar(value=str(datetime.now().month))
        month_entry = tk.Entry(filter_frame, textvariable=self._month_var,
                                font=("Segoe UI", 10), bg=THEME["entry_bg"],
                                fg=THEME["entry_fg"],
                                insertbackground=THEME["text_primary"],
                                relief="flat", width=4)
        month_entry.pack(side="left", padx=(4, 12))

        StyledButton(filter_frame, text="📥 Export Excel",
                     command=self._export_current,
                     font_size=9, padx=12, pady=4).pack(side="right")

        # Summary label
        self._summary_lbl = tk.Label(self, text="", font=("Segoe UI Semibold", 11),
                                      fg=THEME["info"], bg=THEME["bg_medium"],
                                      anchor="w")
        self._summary_lbl.pack(fill="x", padx=20, pady=(0, 4))

        # Treeview (dynamic columns)
        tree_frame = tk.Frame(self, bg=THEME["bg_medium"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        self._tree_container = tree_frame
        self._tree = None
        self._tree_vsb = None

    def _create_tree(self, columns):
        """Recreate the treeview with new columns."""
        if self._tree:
            self._tree.destroy()
        if self._tree_vsb:
            self._tree_vsb.destroy()

        col_ids = [c[0] for c in columns]
        self._tree = ttk.Treeview(self._tree_container, columns=col_ids,
                                   show="headings", height=16)

        for col_id, header, width in columns:
            self._tree.heading(col_id, text=header)
            self._tree.column(col_id, width=width, anchor="center",
                              stretch=True)

        self._tree_vsb = ttk.Scrollbar(self._tree_container, orient="vertical",
                                        command=self._tree.yview)
        self._tree.configure(yscrollcommand=self._tree_vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        self._tree_vsb.pack(side="right", fill="y")

        self._tree.tag_configure("odd", background=THEME["treeview_odd"])
        self._tree.tag_configure("even", background=THEME["treeview_even"])
        self._tree.tag_configure("low_stock", background="#3d1a1a",
                                  foreground=THEME["danger"])

    def _display_data(self, data, columns, summary=""):
        self._current_data = data
        self._current_columns = columns
        self._create_tree(columns)
        self._summary_lbl.config(text=summary)

        keys = [c[0] for c in columns]
        for i, row in enumerate(data):
            tag = "odd" if i % 2 == 0 else "even"
            values = []
            for k in keys:
                v = row.get(k, "")
                if isinstance(v, float):
                    v = f"₹{v:,.2f}" if "price" in k or "amount" in k or "revenue" in k or "cost" in k or "total" in k or "profit" in k or "due" in k or "value" in k else f"{v:,.2f}"
                values.append(v)
            self._tree.insert("", "end", values=values, tags=(tag,))

    # ---- Report Methods ----

    def _report_today_sales(self):
        summary = report_service.get_today_sales()
        detail = report_service.get_today_sales_detail()
        columns = [
            ("bill_number", "Bill No", 120),
            ("customer_name", "Customer", 140),
            ("grand_total", "Total", 100),
            ("paid_amount", "Paid", 100),
            ("due_amount", "Due", 100),
            ("payment_mode", "Mode", 80),
            ("status", "Status", 80),
        ]
        s = summary or {}
        self._display_data(
            detail, columns,
            f"Today: {int(s.get('total_bills', 0))} bills | "
            f"Revenue: ₹{float(s.get('total_revenue', 0)):,.2f} | "
            f"Collected: ₹{float(s.get('total_collected', 0)):,.2f} | "
            f"Due: ₹{float(s.get('total_due', 0)):,.2f}"
        )

    def _report_monthly_sales(self):
        year = int(self._year_var.get() or datetime.now().year)
        month = int(self._month_var.get() or datetime.now().month)
        summary = report_service.get_monthly_sales(year, month)
        detail = report_service.get_monthly_sales_detail(year, month)
        columns = [
            ("bill_number", "Bill No", 120),
            ("customer_name", "Customer", 140),
            ("sale_date", "Date", 120),
            ("grand_total", "Total", 100),
            ("paid_amount", "Paid", 100),
            ("due_amount", "Due", 100),
        ]
        s = summary or {}
        self._display_data(
            detail, columns,
            f"Month {month}/{year}: {int(s.get('total_bills', 0))} bills | "
            f"Revenue: ₹{float(s.get('total_revenue', 0)):,.2f}"
        )

    def _report_yearly_sales(self):
        year = int(self._year_var.get() or datetime.now().year)
        detail = report_service.get_yearly_sales_detail(year)
        columns = [
            ("month", "Month", 80),
            ("total_bills", "Bills", 80),
            ("total_revenue", "Revenue", 120),
            ("total_collected", "Collected", 120),
            ("total_due", "Due", 120),
        ]
        summary = report_service.get_yearly_sales(year)
        s = summary or {}
        self._display_data(
            detail, columns,
            f"Year {year}: {int(s.get('total_bills', 0))} bills | "
            f"Revenue: ₹{float(s.get('total_revenue', 0)):,.2f}"
        )

    def _report_inventory(self):
        data = report_service.get_inventory_report()
        columns = [
            ("product_id", "ID", 50),
            ("product_name", "Product", 180),
            ("category_name", "Category", 110),
            ("stock", "Stock", 70),
            ("unit", "Unit", 60),
            ("purchase_price", "Buy Price", 100),
            ("selling_price", "Sell Price", 100),
            ("stock_cost_value", "Cost Value", 110),
        ]
        self._display_data(data, columns, f"Total Products: {len(data)}")

    def _report_low_stock(self):
        data = report_service.get_low_stock_report()
        columns = [
            ("product_id", "ID", 50),
            ("product_name", "Product", 180),
            ("category_name", "Category", 110),
            ("stock", "Current Stock", 100),
            ("reorder_level", "Reorder Level", 100),
            ("shortage", "Shortage", 80),
        ]
        self._display_data(data, columns, f"⚠ {len(data)} products below reorder level")

    def _report_best_selling(self):
        data = report_service.get_best_selling_products(20)
        columns = [
            ("product_id", "ID", 50),
            ("product_name", "Product", 180),
            ("category_name", "Category", 110),
            ("total_qty_sold", "Qty Sold", 90),
            ("total_revenue", "Revenue", 120),
        ]
        self._display_data(data, columns, f"Top {len(data)} Best Selling Products")

    def _report_profit(self):
        data = report_service.get_product_profit_report()
        columns = [
            ("product_id", "ID", 50),
            ("product_name", "Product", 160),
            ("total_sold_qty", "Sold Qty", 80),
            ("total_sale_revenue", "Sale Revenue", 110),
            ("total_purchase_cost", "Purchase Cost", 110),
            ("profit", "Profit", 110),
        ]
        self._display_data(data, columns, "Product Profit Report")

    def _report_supplier(self):
        data = report_service.get_supplier_purchase_report()
        columns = [
            ("supplier_id", "ID", 50),
            ("supplier_name", "Supplier", 180),
            ("phone", "Phone", 120),
            ("total_purchases", "Purchases", 90),
            ("total_amount", "Total Amount", 130),
        ]
        self._display_data(data, columns, "Supplier Purchase Report")

    def _report_customer(self):
        data = report_service.get_customer_purchase_report()
        columns = [
            ("customer_id", "ID", 50),
            ("customer_name", "Customer", 180),
            ("phone", "Phone", 120),
            ("total_bills", "Bills", 80),
            ("total_amount", "Total Amount", 120),
            ("total_due", "Due", 100),
        ]
        self._display_data(data, columns, "Customer Purchase History")

    def _report_dues(self):
        data = report_service.get_outstanding_due_report()
        columns = [
            ("bill_number", "Bill No", 120),
            ("customer_name", "Customer", 160),
            ("phone", "Phone", 120),
            ("grand_total", "Bill Total", 110),
            ("paid_amount", "Paid", 100),
            ("due_amount", "Due", 100),
        ]
        total_due = sum(float(r.get("due_amount", 0)) for r in data)
        self._display_data(
            data, columns,
            f"Outstanding Dues: {len(data)} bills | Total: ₹{total_due:,.2f}"
        )

    def _export_current(self):
        if not self._current_data:
            messagebox.showinfo("No Data", "Run a report first, then export.")
            return
        try:
            path = export_to_excel(
                self._current_data, self._current_columns,
                sheet_name="Report", title="Report"
            )
            if self.status_bar:
                self.status_bar.success(f"Exported to {path}")
            messagebox.showinfo("Export", f"Report exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
