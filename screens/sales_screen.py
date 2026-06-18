# ==============================================================
# Sales / Billing Screen — Customer lookup, product billing, payment
# ==============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME, PAYMENT_MODES
from screens.widgets import StyledButton
from services import customer_service, inventory_service, sales_service
from utils.validators import (validate_phone, validate_not_empty,
                               validate_positive_int, validate_positive_decimal)
from utils.pdf_generator import generate_sale_invoice


class SalesScreen(tk.Frame):

    def __init__(self, parent, status_bar=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_medium"], **kwargs)
        self.status_bar = status_bar
        self._customer = None
        self._cart_items = []
        self._cart_counter = 0

        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        tk.Label(self, text="🧾  Sales / Billing", font=("Segoe UI Semibold", 16),
                 fg=THEME["text_primary"], bg=THEME["bg_medium"]).pack(
            anchor="w", padx=20, pady=(16, 6))

        container = tk.Frame(self, bg=THEME["bg_medium"])
        container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        left = tk.Frame(container, bg=THEME["bg_medium"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self._build_customer_section(left)
        self._build_product_search_section(left)

        right = tk.Frame(container, bg=THEME["bg_medium"])
        right.pack(side="right", fill="both", expand=True)

        self._build_cart_section(right)
        self._build_billing_section(right)

    # ---- Customer Section ----
    def _build_customer_section(self, parent):
        frame = tk.LabelFrame(parent, text="  Customer  ",
                               font=("Segoe UI Semibold", 10),
                               fg=THEME["text_primary"], bg=THEME["bg_card"],
                               bd=1, relief="groove")
        frame.pack(fill="x", pady=(0, 10))

        row1 = tk.Frame(frame, bg=THEME["bg_card"])
        row1.pack(fill="x", padx=12, pady=8)
        tk.Label(row1, text="Phone:", font=("Segoe UI", 10),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"], width=10,
                 anchor="w").pack(side="left")
        self._cust_phone = tk.Entry(row1, font=("Segoe UI", 11),
                                     bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                     insertbackground=THEME["text_primary"],
                                     relief="flat", width=18)
        self._cust_phone.pack(side="left", padx=(0, 8))
        StyledButton(row1, text="🔍 Lookup", command=self._lookup_customer,
                     font_size=9, padx=10, pady=4).pack(side="left")

        self._cust_status = tk.Label(frame, text="", font=("Segoe UI", 9),
                                      fg=THEME["text_muted"], bg=THEME["bg_card"])
        self._cust_status.pack(anchor="w", padx=12)

        detail = tk.Frame(frame, bg=THEME["bg_card"])
        detail.pack(fill="x", padx=12, pady=(4, 10))

        for label_text, attr in [("Name:", "_cust_name"), ("Address:", "_cust_addr")]:
            r = tk.Frame(detail, bg=THEME["bg_card"])
            r.pack(fill="x", pady=2)
            tk.Label(r, text=label_text, font=("Segoe UI", 9),
                     fg=THEME["text_secondary"], bg=THEME["bg_card"],
                     width=10, anchor="w").pack(side="left")
            entry = tk.Entry(r, font=("Segoe UI", 10), bg=THEME["entry_bg"],
                              fg=THEME["entry_fg"],
                              insertbackground=THEME["text_primary"],
                              relief="flat", width=28)
            entry.pack(side="left", fill="x", expand=True)
            setattr(self, attr, entry)

    # ---- Product Search Section ----
    def _build_product_search_section(self, parent):
        frame = tk.LabelFrame(parent, text="  Add Product  ",
                               font=("Segoe UI Semibold", 10),
                               fg=THEME["text_primary"], bg=THEME["bg_card"],
                               bd=1, relief="groove")
        frame.pack(fill="both", expand=True, pady=(0, 10))

        inner = tk.Frame(frame, bg=THEME["bg_card"])
        inner.pack(fill="x", padx=12, pady=10)

        # Search
        r0 = tk.Frame(inner, bg=THEME["bg_card"])
        r0.pack(fill="x", pady=2)
        tk.Label(r0, text="Search:", font=("Segoe UI", 9),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"],
                 width=10, anchor="w").pack(side="left")
        self._search_entry = tk.Entry(r0, font=("Segoe UI", 10),
                                       bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                       insertbackground=THEME["text_primary"],
                                       relief="flat", width=20)
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        StyledButton(r0, text="🔍", command=self._search_product,
                     font_size=9, padx=8, pady=3).pack(side="left")

        self._search_entry.bind("<Return>", lambda e: self._search_product())

        # Search results listbox
        self._search_listbox = tk.Listbox(
            inner, font=("Segoe UI", 10), bg=THEME["entry_bg"],
            fg=THEME["entry_fg"], selectbackground=THEME["accent"],
            selectforeground=THEME["text_primary"], height=4, relief="flat",
            borderwidth=0,
        )
        self._search_listbox.pack(fill="x", pady=(4, 6))
        self._search_listbox.bind("<<ListboxSelect>>", self._on_product_select)
        self._search_results = []

        # Product info
        info_frame = tk.Frame(inner, bg=THEME["bg_card"])
        info_frame.pack(fill="x")

        self._sel_product_lbl = tk.Label(
            info_frame, text="No product selected", font=("Segoe UI", 9),
            fg=THEME["text_muted"], bg=THEME["bg_card"], anchor="w",
        )
        self._sel_product_lbl.pack(fill="x")

        qty_row = tk.Frame(inner, bg=THEME["bg_card"])
        qty_row.pack(fill="x", pady=(6, 0))
        tk.Label(qty_row, text="Qty:", font=("Segoe UI", 9),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"],
                 width=10, anchor="w").pack(side="left")
        self._sale_qty = tk.Entry(qty_row, font=("Segoe UI", 10),
                                   bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                   insertbackground=THEME["text_primary"],
                                   relief="flat", width=8)
        self._sale_qty.pack(side="left", padx=(0, 10))

        StyledButton(qty_row, text="➕ Add to Bill",
                     command=self._add_to_bill,
                     bg_color=THEME["success"], hover_color="#38e882",
                     font_size=9, padx=12, pady=4).pack(side="left")

        self._selected_product = None

    # ---- Cart Section ----
    def _build_cart_section(self, parent):
        frame = tk.LabelFrame(parent, text="  Bill Items  ",
                               font=("Segoe UI Semibold", 10),
                               fg=THEME["text_primary"], bg=THEME["bg_card"],
                               bd=1, relief="groove")
        frame.pack(fill="both", expand=True, pady=(0, 10))

        tree_frame = tk.Frame(frame, bg=THEME["bg_card"])
        tree_frame.pack(fill="both", expand=True, padx=8, pady=8)

        cols = ("sno", "product", "qty", "rate", "amount")
        self._bill_tree = ttk.Treeview(tree_frame, columns=cols,
                                        show="headings", height=8)
        for col, hd, w, anchor in [
            ("sno", "S.No", 40, "center"),
            ("product", "Product", 150, "w"),
            ("qty", "Qty", 50, "center"),
            ("rate", "Rate", 80, "e"),
            ("amount", "Amount", 90, "e"),
        ]:
            self._bill_tree.heading(col, text=hd)
            self._bill_tree.column(col, width=w, anchor=anchor, stretch=col == "product")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self._bill_tree.yview)
        self._bill_tree.configure(yscrollcommand=vsb.set)
        self._bill_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._bill_tree.tag_configure("odd", background=THEME["treeview_odd"])
        self._bill_tree.tag_configure("even", background=THEME["treeview_even"])

        btn_row = tk.Frame(frame, bg=THEME["bg_card"])
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        StyledButton(btn_row, text="🗑 Remove",
                     command=self._remove_selected,
                     bg_color=THEME["danger"], hover_color="#ff6b6b",
                     font_size=9, padx=10, pady=3).pack(side="left")
        StyledButton(btn_row, text="🔄 Clear",
                     command=self._clear_bill,
                     bg_color=THEME["text_muted"], hover_color="#8888aa",
                     font_size=9, padx=10, pady=3).pack(side="left", padx=6)

    # ---- Billing Summary ----
    def _build_billing_section(self, parent):
        frame = tk.LabelFrame(parent, text="  Billing  ",
                               font=("Segoe UI Semibold", 10),
                               fg=THEME["text_primary"], bg=THEME["bg_card"],
                               bd=1, relief="groove")
        frame.pack(fill="x")

        inner = tk.Frame(frame, bg=THEME["bg_card"])
        inner.pack(fill="x", padx=12, pady=10)

        # Subtotal
        self._add_summary_row(inner, "Subtotal:", "_subtotal_lbl")

        # Discount
        r_disc = tk.Frame(inner, bg=THEME["bg_card"])
        r_disc.pack(fill="x", pady=2)
        tk.Label(r_disc, text="Discount %:", font=("Segoe UI", 10),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"],
                 anchor="w").pack(side="left")
        self._disc_entry = tk.Entry(r_disc, font=("Segoe UI", 10),
                                     bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                     insertbackground=THEME["text_primary"],
                                     relief="flat", width=8, justify="right")
        self._disc_entry.insert(0, "0")
        self._disc_entry.pack(side="right")
        self._disc_entry.bind("<KeyRelease>", lambda e: self._update_billing())

        # GST
        self._add_summary_row(inner, "GST:", "_gst_lbl")

        # Grand Total
        r_gt = tk.Frame(inner, bg=THEME["bg_card"])
        r_gt.pack(fill="x", pady=(6, 4))
        tk.Label(r_gt, text="Grand Total:", font=("Segoe UI Semibold", 12),
                 fg=THEME["primary"], bg=THEME["bg_card"]).pack(side="left")
        self._grand_total_lbl = tk.Label(r_gt, text="₹ 0.00",
                                          font=("Segoe UI Bold", 14),
                                          fg=THEME["primary"], bg=THEME["bg_card"])
        self._grand_total_lbl.pack(side="right")

        # Payment mode
        r_pm = tk.Frame(inner, bg=THEME["bg_card"])
        r_pm.pack(fill="x", pady=(6, 2))
        tk.Label(r_pm, text="Payment:", font=("Segoe UI", 10),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"]).pack(side="left")
        self._pay_mode = tk.StringVar(value="Cash")
        for mode in PAYMENT_MODES:
            ttk.Radiobutton(r_pm, text=mode, variable=self._pay_mode,
                            value=mode).pack(side="left", padx=4)

        # Paid amount
        r_paid = tk.Frame(inner, bg=THEME["bg_card"])
        r_paid.pack(fill="x", pady=2)
        tk.Label(r_paid, text="Paid (₹):", font=("Segoe UI", 10),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"]).pack(side="left")
        self._paid_entry = tk.Entry(r_paid, font=("Segoe UI", 10),
                                     bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                     insertbackground=THEME["text_primary"],
                                     relief="flat", width=12, justify="right")
        self._paid_entry.insert(0, "0")
        self._paid_entry.pack(side="right")
        self._paid_entry.bind("<KeyRelease>", lambda e: self._update_billing())

        # Due
        self._add_summary_row(inner, "Due:", "_due_lbl", fg=THEME["warning"])

        # Generate Bill button
        btn_row = tk.Frame(inner, bg=THEME["bg_card"])
        btn_row.pack(fill="x", pady=(12, 0))
        StyledButton(btn_row, text="🧾  Generate Bill",
                     command=self._generate_bill,
                     bg_color=THEME["primary"], hover_color=THEME["primary_hover"],
                     font_size=11, padx=20, pady=8).pack(fill="x")

    def _add_summary_row(self, parent, label_text, attr, fg=None):
        r = tk.Frame(parent, bg=THEME["bg_card"])
        r.pack(fill="x", pady=2)
        tk.Label(r, text=label_text, font=("Segoe UI", 10),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"]).pack(side="left")
        lbl = tk.Label(r, text="₹ 0.00", font=("Segoe UI Semibold", 11),
                        fg=fg or THEME["text_primary"], bg=THEME["bg_card"])
        lbl.pack(side="right")
        setattr(self, attr, lbl)

    # ---------------------------------------------------------------- LOGIC

    def _lookup_customer(self):
        phone = self._cust_phone.get().strip()
        valid, result = validate_phone(phone)
        if not valid:
            self._cust_status.config(text=result, fg=THEME["danger"])
            return

        customer = customer_service.find_by_phone(result)
        if customer:
            self._customer = customer
            self._cust_name.delete(0, "end")
            self._cust_name.insert(0, customer["customer_name"])
            self._cust_addr.delete(0, "end")
            self._cust_addr.insert(0, customer.get("address", ""))
            self._cust_status.config(text="✓ Customer Found!", fg=THEME["success"])
        else:
            self._customer = None
            self._cust_name.delete(0, "end")
            self._cust_addr.delete(0, "end")
            self._cust_status.config(text="New customer — fill in details below",
                                      fg=THEME["warning"])

    def _search_product(self):
        keyword = self._search_entry.get().strip()
        if not keyword:
            return
        results = inventory_service.search_product(keyword)
        self._search_results = results
        self._search_listbox.delete(0, "end")
        for p in results:
            self._search_listbox.insert(
                "end",
                f"{p['product_name']}  |  Stock: {p['stock']}  |  ₹{float(p['selling_price']):,.2f}"
            )
        if not results:
            self._search_listbox.insert("end", "No products found")

    def _on_product_select(self, event):
        sel = self._search_listbox.curselection()
        if not sel or not self._search_results:
            return
        idx = sel[0]
        if idx >= len(self._search_results):
            return
        p = self._search_results[idx]
        self._selected_product = p
        self._sel_product_lbl.config(
            text=f"✓ {p['product_name']}  |  Stock: {p['stock']}  |  "
                 f"₹{float(p['selling_price']):,.2f}",
            fg=THEME["success"],
        )

    def _add_to_bill(self):
        if not self._selected_product:
            messagebox.showwarning("Select Product", "Search and select a product first.")
            return
        valid, qty = validate_positive_int(self._sale_qty.get(), "Quantity")
        if not valid:
            messagebox.showwarning("Validation", qty)
            return

        p = self._selected_product
        if qty > p["stock"]:
            messagebox.showwarning(
                "Insufficient Stock",
                f"Available stock for '{p['product_name']}': {p['stock']}\n"
                f"Requested: {qty}"
            )
            return

        amount = qty * float(p["selling_price"])
        self._cart_counter += 1
        self._cart_items.append({
            "sno": self._cart_counter,
            "product_id": p["product_id"],
            "product_name": p["product_name"],
            "quantity": qty,
            "selling_price": float(p["selling_price"]),
            "amount": amount,
            "stock": p["stock"],
            "gst_rate": float(p.get("gst_rate", 18.0)),
            "unit": p.get("unit", "Pcs"),
        })
        self._refresh_bill()
        self._update_billing()

        self._sale_qty.delete(0, "end")
        self._selected_product = None
        self._sel_product_lbl.config(text="No product selected",
                                      fg=THEME["text_muted"])
        self._search_entry.delete(0, "end")
        self._search_listbox.delete(0, "end")
        self._search_entry.focus()

        if self.status_bar:
            self.status_bar.info(f"Added {p['product_name']} × {qty}")

    def _refresh_bill(self):
        self._bill_tree.delete(*self._bill_tree.get_children())
        for i, item in enumerate(self._cart_items):
            tag = "odd" if i % 2 == 0 else "even"
            self._bill_tree.insert("", "end", values=(
                item["sno"], item["product_name"], item["quantity"],
                f"₹{item['selling_price']:,.2f}", f"₹{item['amount']:,.2f}",
            ), tags=(tag,))

    def _update_billing(self):
        subtotal = sum(item["amount"] for item in self._cart_items)

        try:
            disc_pct = float(self._disc_entry.get() or 0)
        except ValueError:
            disc_pct = 0
        discount_amt = round(subtotal * disc_pct / 100, 2)
        after_disc = subtotal - discount_amt

        gst_total = 0.0
        for item in self._cart_items:
            gst_total += round(item["amount"] * item.get("gst_rate", 18.0) / 100, 2)

        grand_total = round(after_disc + gst_total, 2)

        try:
            paid = float(self._paid_entry.get() or 0)
        except ValueError:
            paid = 0
        due = max(grand_total - paid, 0)

        self._subtotal_lbl.config(text=f"₹ {subtotal:,.2f}")
        self._gst_lbl.config(text=f"₹ {gst_total:,.2f}")
        self._grand_total_lbl.config(text=f"₹ {grand_total:,.2f}")
        self._due_lbl.config(text=f"₹ {due:,.2f}")

    def _remove_selected(self):
        sel = self._bill_tree.selection()
        if not sel:
            return
        idx = self._bill_tree.index(sel[0])
        self._cart_items.pop(idx)
        self._refresh_bill()
        self._update_billing()

    def _clear_bill(self):
        self._cart_items.clear()
        self._cart_counter = 0
        self._refresh_bill()
        self._update_billing()

    def _generate_bill(self):
        if not self._cart_items:
            messagebox.showwarning("Empty Bill", "Add at least one product.")
            return

        # Ensure customer
        if not self._customer:
            name = self._cust_name.get().strip()
            phone = self._cust_phone.get().strip()
            valid, phone_clean = validate_phone(phone)
            if not valid:
                messagebox.showwarning("Customer", phone_clean)
                return
            v, msg = validate_not_empty(name, "Customer Name")
            if not v:
                messagebox.showwarning("Customer", msg)
                return
            addr = self._cust_addr.get().strip()
            cid = customer_service.create_customer(name, phone_clean, addr)
            self._customer = customer_service.get_customer(cid)

        try:
            disc_pct = float(self._disc_entry.get() or 0)
        except ValueError:
            disc_pct = 0
        try:
            paid = float(self._paid_entry.get() or 0)
        except ValueError:
            paid = 0

        payment_mode = self._pay_mode.get()

        try:
            result = sales_service.save_sale(
                customer_id=self._customer["customer_id"],
                items=self._cart_items,
                discount_pct=disc_pct,
                paid_amount=paid,
                payment_mode=payment_mode,
            )
        except sales_service.InsufficientStockError as e:
            messagebox.showerror("Stock Error", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save sale:\n{e}")
            return

        # Generate PDF
        try:
            sale_full = sales_service.get_sale(result["sale_id"])
            pdf_path = generate_sale_invoice(
                sale_full, sale_full["items"], self._customer
            )
            if self.status_bar:
                self.status_bar.success(
                    f"Bill {result['bill_number']} generated! PDF: {pdf_path}"
                )
        except Exception:
            if self.status_bar:
                self.status_bar.success(
                    f"Bill {result['bill_number']} generated! (PDF skipped)"
                )

        due_msg = ""
        if result["due_amount"] > 0:
            due_msg = f"\nDue Amount: ₹ {result['due_amount']:,.2f}"

        messagebox.showinfo(
            "Bill Generated",
            f"Bill Number: {result['bill_number']}\n"
            f"Grand Total: ₹ {result['grand_total']:,.2f}\n"
            f"Paid: ₹ {result['paid_amount']:,.2f}"
            f"{due_msg}\n\n"
            f"Inventory updated automatically."
        )

        self._reset_form()

    def _reset_form(self):
        self._customer = None
        self._cart_items.clear()
        self._cart_counter = 0
        self._selected_product = None
        self._cust_phone.delete(0, "end")
        self._cust_name.delete(0, "end")
        self._cust_addr.delete(0, "end")
        self._cust_status.config(text="")
        self._search_entry.delete(0, "end")
        self._search_listbox.delete(0, "end")
        self._sel_product_lbl.config(text="No product selected",
                                      fg=THEME["text_muted"])
        self._sale_qty.delete(0, "end")
        self._disc_entry.delete(0, "end")
        self._disc_entry.insert(0, "0")
        self._paid_entry.delete(0, "end")
        self._paid_entry.insert(0, "0")
        self._refresh_bill()
        self._update_billing()
