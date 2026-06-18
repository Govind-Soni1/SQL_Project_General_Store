# ==============================================================
# Customer History Screen — view purchases, dues, collect payments
# ==============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME
from screens.widgets import StyledButton
from services import customer_service, sales_service
from utils.validators import validate_phone, validate_positive_decimal


class CustomerHistoryScreen(tk.Frame):

    def __init__(self, parent, status_bar=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_medium"], **kwargs)
        self.status_bar = status_bar
        self._customer = None
        self._build_ui()

    def _build_ui(self):
        tk.Label(self, text="👤  Customer History", font=("Segoe UI Semibold", 16),
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
        StyledButton(search_frame, text="🔍 Find", command=self._find_customer,
                     font_size=9, padx=10, pady=4).pack(side="left")
        StyledButton(search_frame, text="📋 All Customers",
                     command=self._show_all_customers,
                     font_size=9, padx=10, pady=4).pack(side="left", padx=6)

        # Customer info
        self._info_lbl = tk.Label(self, text="", font=("Segoe UI", 10),
                                   fg=THEME["text_secondary"], bg=THEME["bg_medium"],
                                   anchor="w")
        self._info_lbl.pack(fill="x", padx=20)

        # Summary
        self._summary_lbl = tk.Label(self, text="", font=("Segoe UI Semibold", 10),
                                      fg=THEME["info"], bg=THEME["bg_medium"],
                                      anchor="w")
        self._summary_lbl.pack(fill="x", padx=20, pady=(2, 6))

        # Treeview
        tree_frame = tk.Frame(self, bg=THEME["bg_medium"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        cols = ("bill", "date", "total", "paid", "due", "mode", "status")
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=12)
        for col, hd, w in [
            ("bill", "Bill No", 120), ("date", "Date", 120),
            ("total", "Total", 100), ("paid", "Paid", 100),
            ("due", "Due", 100), ("mode", "Payment", 80),
            ("status", "Status", 80),
        ]:
            self._tree.heading(col, text=hd)
            self._tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree.tag_configure("odd", background=THEME["treeview_odd"])
        self._tree.tag_configure("even", background=THEME["treeview_even"])
        self._tree.tag_configure("due", background="#3d2a1a",
                                  foreground=THEME["warning"])

        # Collect payment button
        btn_frame = tk.Frame(self, bg=THEME["bg_medium"])
        btn_frame.pack(fill="x", padx=20, pady=(0, 14))
        StyledButton(btn_frame, text="💰 Collect Due Payment",
                     command=self._collect_payment,
                     bg_color=THEME["success"], hover_color="#38e882",
                     font_size=10, padx=14, pady=6).pack(side="left")

    def _find_customer(self):
        phone = self._phone_entry.get().strip()
        valid, result = validate_phone(phone)
        if not valid:
            messagebox.showwarning("Validation", result)
            return

        customer = customer_service.find_by_phone(result)
        if not customer:
            self._info_lbl.config(text="Customer not found.", fg=THEME["danger"])
            return

        self._customer = customer
        self._info_lbl.config(
            text=f"Customer: {customer['customer_name']} | Phone: {customer['phone']} | "
                 f"Address: {customer.get('address', 'N/A')}",
            fg=THEME["text_primary"],
        )
        self._load_history(customer["customer_id"])

    def _show_all_customers(self):
        customers = customer_service.get_all_customers()
        self._tree.delete(*self._tree.get_children())
        self._info_lbl.config(text=f"All Customers ({len(customers)})",
                               fg=THEME["text_primary"])

        # Repurpose tree for customer list
        for col in self._tree["columns"]:
            self._tree.heading(col, text="")
        self._tree.heading("bill", text="ID")
        self._tree.heading("date", text="Name")
        self._tree.heading("total", text="Phone")
        self._tree.heading("paid", text="Total Spent")
        self._tree.heading("due", text="Total Due")
        self._tree.heading("mode", text="Bills")
        self._tree.heading("status", text="")

        for i, c in enumerate(customers):
            total = customer_service.get_customer_total_spent(c["customer_id"])
            due = customer_service.get_customer_total_due(c["customer_id"])
            history = customer_service.get_customer_history(c["customer_id"])
            tag = "odd" if i % 2 == 0 else "even"
            self._tree.insert("", "end", values=(
                c["customer_id"], c["customer_name"], c["phone"],
                f"₹{total:,.2f}", f"₹{due:,.2f}", len(history), "",
            ), tags=(tag,))

        self._summary_lbl.config(text="")

    def _load_history(self, customer_id):
        sales = customer_service.get_customer_history(customer_id)
        total_spent = customer_service.get_customer_total_spent(customer_id)
        total_due = customer_service.get_customer_total_due(customer_id)

        # Reset headers
        for col, hd in [("bill", "Bill No"), ("date", "Date"),
                         ("total", "Total"), ("paid", "Paid"),
                         ("due", "Due"), ("mode", "Payment"),
                         ("status", "Status")]:
            self._tree.heading(col, text=hd)

        self._tree.delete(*self._tree.get_children())
        for i, s in enumerate(sales):
            due = float(s.get("due_amount", 0))
            tag = "due" if due > 0 else ("odd" if i % 2 == 0 else "even")
            self._tree.insert("", "end", values=(
                s["bill_number"], str(s.get("sale_date", "")),
                f"₹{float(s['grand_total']):,.2f}",
                f"₹{float(s['paid_amount']):,.2f}",
                f"₹{due:,.2f}", s.get("payment_mode", ""),
                s.get("status", ""),
            ), tags=(tag,), iid=str(s["sale_id"]))

        self._summary_lbl.config(
            text=f"Total Bills: {len(sales)} | Spent: ₹{total_spent:,.2f} | "
                 f"Outstanding Due: ₹{total_due:,.2f}"
        )

    def _collect_payment(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Select", "Select a bill with outstanding due.")
            return

        sale_id = int(sel[0])
        sale = sales_service.get_sale(sale_id)
        if not sale or float(sale["due_amount"]) <= 0:
            messagebox.showinfo("No Due", "This bill has no outstanding due.")
            return

        # Payment dialog
        dlg = tk.Toplevel(self)
        dlg.title("Collect Payment")
        dlg.configure(bg=THEME["bg_card"])
        dlg.geometry("320x200")
        dlg.resizable(False, False)
        dlg.grab_set()

        due = float(sale["due_amount"])
        tk.Label(dlg, text=f"Bill: {sale['bill_number']}",
                 font=("Segoe UI Semibold", 11),
                 fg=THEME["text_primary"], bg=THEME["bg_card"]).pack(pady=(14, 4))
        tk.Label(dlg, text=f"Outstanding Due: ₹{due:,.2f}",
                 font=("Segoe UI", 10),
                 fg=THEME["warning"], bg=THEME["bg_card"]).pack()

        tk.Label(dlg, text="Amount to collect:", font=("Segoe UI", 10),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"]).pack(pady=(10, 2))
        amt_entry = tk.Entry(dlg, font=("Segoe UI", 11), bg=THEME["entry_bg"],
                              fg=THEME["entry_fg"],
                              insertbackground=THEME["text_primary"],
                              relief="flat", width=14, justify="center")
        amt_entry.pack()
        amt_entry.insert(0, str(due))

        def do_collect():
            valid, amount = validate_positive_decimal(amt_entry.get(), "Amount")
            if not valid:
                messagebox.showwarning("Validation", amount, parent=dlg)
                return
            try:
                result = sales_service.record_due_payment(sale_id, amount)
                messagebox.showinfo(
                    "Payment Recorded",
                    f"Collected: ₹{amount:,.2f}\n"
                    f"Remaining Due: ₹{result['new_due']:,.2f}",
                    parent=dlg,
                )
                dlg.destroy()
                if self._customer:
                    self._load_history(self._customer["customer_id"])
                if self.status_bar:
                    self.status_bar.success(f"Payment of ₹{amount:,.2f} collected")
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)

        StyledButton(dlg, text="💰 Collect", command=do_collect,
                     bg_color=THEME["success"], hover_color="#38e882",
                     font_size=10, padx=16, pady=6).pack(pady=14)

        self.wait_window(dlg)
