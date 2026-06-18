# ==============================================================
# Purchase Screen — Supplier lookup, product entry, save purchase
# ==============================================================

import tkinter as tk
from tkinter import ttk, messagebox
from config import THEME, PRODUCT_UNITS
from screens.widgets import StyledButton, SearchEntry
from services import supplier_service, inventory_service, purchase_service
from utils.validators import validate_phone, validate_not_empty, validate_positive_int, validate_positive_decimal
from utils.pdf_generator import generate_purchase_receipt


class PurchaseScreen(tk.Frame):

    def __init__(self, parent, status_bar=None, **kwargs):
        super().__init__(parent, bg=THEME["bg_medium"], **kwargs)
        self.status_bar = status_bar
        self._supplier = None
        self._cart_items = []       # list of dicts
        self._cart_counter = 0

        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        # Title
        tk.Label(self, text="📦  Purchase Entry", font=("Segoe UI Semibold", 16),
                 fg=THEME["text_primary"], bg=THEME["bg_medium"]).pack(
            anchor="w", padx=20, pady=(16, 6))

        # Main container
        container = tk.Frame(self, bg=THEME["bg_medium"])
        container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # ---- Left: Supplier + Product entry ----
        left = tk.Frame(container, bg=THEME["bg_medium"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self._build_supplier_section(left)
        self._build_product_entry_section(left)

        # ---- Right: Cart + Summary ----
        right = tk.Frame(container, bg=THEME["bg_medium"])
        right.pack(side="right", fill="both", expand=True)

        self._build_cart_section(right)
        self._build_summary_section(right)

    # ---- Supplier Section ----
    def _build_supplier_section(self, parent):
        frame = tk.LabelFrame(parent, text="  Supplier  ", font=("Segoe UI Semibold", 10),
                               fg=THEME["text_primary"], bg=THEME["bg_card"],
                               bd=1, relief="groove")
        frame.pack(fill="x", pady=(0, 10))

        row1 = tk.Frame(frame, bg=THEME["bg_card"])
        row1.pack(fill="x", padx=12, pady=8)
        tk.Label(row1, text="Phone:", font=("Segoe UI", 10),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"], width=10,
                 anchor="w").pack(side="left")
        self._sup_phone = tk.Entry(row1, font=("Segoe UI", 11),
                                    bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                    insertbackground=THEME["text_primary"],
                                    relief="flat", width=18)
        self._sup_phone.pack(side="left", padx=(0, 8))
        StyledButton(row1, text="🔍 Lookup", command=self._lookup_supplier,
                     font_size=9, padx=10, pady=4).pack(side="left")

        self._sup_status = tk.Label(frame, text="", font=("Segoe UI", 9),
                                     fg=THEME["text_muted"], bg=THEME["bg_card"])
        self._sup_status.pack(anchor="w", padx=12)

        # Detail fields
        detail = tk.Frame(frame, bg=THEME["bg_card"])
        detail.pack(fill="x", padx=12, pady=(4, 10))

        fields = [("Name:", "_sup_name"), ("Address:", "_sup_addr"),
                  ("GST No:", "_sup_gst")]
        for label_text, attr in fields:
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

    # ---- Product Entry Section ----
    def _build_product_entry_section(self, parent):
        frame = tk.LabelFrame(parent, text="  Add Product  ",
                               font=("Segoe UI Semibold", 10),
                               fg=THEME["text_primary"], bg=THEME["bg_card"],
                               bd=1, relief="groove")
        frame.pack(fill="x", pady=(0, 10))

        inner = tk.Frame(frame, bg=THEME["bg_card"])
        inner.pack(fill="x", padx=12, pady=10)

        # Product Name
        r1 = tk.Frame(inner, bg=THEME["bg_card"])
        r1.pack(fill="x", pady=2)
        tk.Label(r1, text="Product:", font=("Segoe UI", 9),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"],
                 width=10, anchor="w").pack(side="left")
        self._prod_name = tk.Entry(r1, font=("Segoe UI", 10),
                                    bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                    insertbackground=THEME["text_primary"],
                                    relief="flat", width=28)
        self._prod_name.pack(side="left", fill="x", expand=True)

        # Quantity + Rate
        r2 = tk.Frame(inner, bg=THEME["bg_card"])
        r2.pack(fill="x", pady=2)
        tk.Label(r2, text="Qty:", font=("Segoe UI", 9),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"],
                 width=10, anchor="w").pack(side="left")
        self._prod_qty = tk.Entry(r2, font=("Segoe UI", 10),
                                   bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                   insertbackground=THEME["text_primary"],
                                   relief="flat", width=8)
        self._prod_qty.pack(side="left", padx=(0, 10))
        tk.Label(r2, text="Rate:", font=("Segoe UI", 9),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"],
                 anchor="w").pack(side="left")
        self._prod_rate = tk.Entry(r2, font=("Segoe UI", 10),
                                    bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                    insertbackground=THEME["text_primary"],
                                    relief="flat", width=10)
        self._prod_rate.pack(side="left")

        # Add button
        btn_row = tk.Frame(inner, bg=THEME["bg_card"])
        btn_row.pack(fill="x", pady=(8, 0))
        StyledButton(btn_row, text="➕ Add to Cart", command=self._add_to_cart,
                     bg_color=THEME["success"], hover_color="#38e882",
                     font_size=10, padx=14, pady=5).pack(side="left")

    # ---- Cart Section ----
    def _build_cart_section(self, parent):
        frame = tk.LabelFrame(parent, text="  Purchase Items  ",
                               font=("Segoe UI Semibold", 10),
                               fg=THEME["text_primary"], bg=THEME["bg_card"],
                               bd=1, relief="groove")
        frame.pack(fill="both", expand=True, pady=(0, 10))

        tree_frame = tk.Frame(frame, bg=THEME["bg_card"])
        tree_frame.pack(fill="both", expand=True, padx=8, pady=8)

        cols = ("sno", "product", "qty", "rate", "amount")
        self._cart_tree = ttk.Treeview(tree_frame, columns=cols,
                                        show="headings", height=8)
        for col, hd, w, anchor in [
            ("sno", "S.No", 40, "center"),
            ("product", "Product", 160, "w"),
            ("qty", "Qty", 55, "center"),
            ("rate", "Rate", 80, "e"),
            ("amount", "Amount", 90, "e"),
        ]:
            self._cart_tree.heading(col, text=hd)
            self._cart_tree.column(col, width=w, anchor=anchor, stretch=col == "product")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                             command=self._cart_tree.yview)
        self._cart_tree.configure(yscrollcommand=vsb.set)
        self._cart_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._cart_tree.tag_configure("odd", background=THEME["treeview_odd"])
        self._cart_tree.tag_configure("even", background=THEME["treeview_even"])

        # Remove button
        btn_row = tk.Frame(frame, bg=THEME["bg_card"])
        btn_row.pack(fill="x", padx=8, pady=(0, 8))
        StyledButton(btn_row, text="🗑 Remove Selected",
                     command=self._remove_selected,
                     bg_color=THEME["danger"], hover_color="#ff6b6b",
                     font_size=9, padx=10, pady=3).pack(side="left")
        StyledButton(btn_row, text="🔄 Clear All",
                     command=self._clear_cart,
                     bg_color=THEME["text_muted"], hover_color="#8888aa",
                     font_size=9, padx=10, pady=3).pack(side="left", padx=6)

    # ---- Summary Section ----
    def _build_summary_section(self, parent):
        frame = tk.LabelFrame(parent, text="  Summary  ",
                               font=("Segoe UI Semibold", 10),
                               fg=THEME["text_primary"], bg=THEME["bg_card"],
                               bd=1, relief="groove")
        frame.pack(fill="x")

        inner = tk.Frame(frame, bg=THEME["bg_card"])
        inner.pack(fill="x", padx=12, pady=10)

        # Subtotal
        r1 = tk.Frame(inner, bg=THEME["bg_card"])
        r1.pack(fill="x", pady=2)
        tk.Label(r1, text="Subtotal:", font=("Segoe UI", 10),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"],
                 anchor="w").pack(side="left")
        self._subtotal_lbl = tk.Label(r1, text="₹ 0.00",
                                       font=("Segoe UI Semibold", 11),
                                       fg=THEME["text_primary"],
                                       bg=THEME["bg_card"])
        self._subtotal_lbl.pack(side="right")

        # Discount
        r2 = tk.Frame(inner, bg=THEME["bg_card"])
        r2.pack(fill="x", pady=2)
        tk.Label(r2, text="Discount (₹):", font=("Segoe UI", 10),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"],
                 anchor="w").pack(side="left")
        self._discount_entry = tk.Entry(r2, font=("Segoe UI", 10),
                                         bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                         insertbackground=THEME["text_primary"],
                                         relief="flat", width=10, justify="right")
        self._discount_entry.insert(0, "0")
        self._discount_entry.pack(side="right")
        self._discount_entry.bind("<KeyRelease>", lambda e: self._update_summary())

        # Grand Total
        r3 = tk.Frame(inner, bg=THEME["bg_card"])
        r3.pack(fill="x", pady=(6, 2))
        tk.Label(r3, text="Grand Total:", font=("Segoe UI Semibold", 12),
                 fg=THEME["primary"], bg=THEME["bg_card"],
                 anchor="w").pack(side="left")
        self._grand_total_lbl = tk.Label(r3, text="₹ 0.00",
                                          font=("Segoe UI Bold", 14),
                                          fg=THEME["primary"],
                                          bg=THEME["bg_card"])
        self._grand_total_lbl.pack(side="right")

        # Notes
        r4 = tk.Frame(inner, bg=THEME["bg_card"])
        r4.pack(fill="x", pady=(6, 2))
        tk.Label(r4, text="Notes:", font=("Segoe UI", 9),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"],
                 anchor="w").pack(side="left")
        self._notes_entry = tk.Entry(r4, font=("Segoe UI", 10),
                                      bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                      insertbackground=THEME["text_primary"],
                                      relief="flat")
        self._notes_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

        # Save button
        btn_row = tk.Frame(inner, bg=THEME["bg_card"])
        btn_row.pack(fill="x", pady=(12, 0))
        StyledButton(btn_row, text="💾  Save Purchase",
                     command=self._save_purchase,
                     bg_color=THEME["primary"], hover_color=THEME["primary_hover"],
                     font_size=11, padx=20, pady=8).pack(fill="x")

    # ---------------------------------------------------------------- LOGIC

    def _lookup_supplier(self):
        phone = self._sup_phone.get().strip()
        valid, result = validate_phone(phone)
        if not valid:
            self._sup_status.config(text=result, fg=THEME["danger"])
            return

        supplier = supplier_service.find_by_phone(result)
        if supplier:
            self._supplier = supplier
            self._sup_name.delete(0, "end")
            self._sup_name.insert(0, supplier["supplier_name"])
            self._sup_addr.delete(0, "end")
            self._sup_addr.insert(0, supplier.get("address", ""))
            self._sup_gst.delete(0, "end")
            self._sup_gst.insert(0, supplier.get("gst_number", ""))
            self._sup_status.config(text="✓ Supplier Found!", fg=THEME["success"])
            if self.status_bar:
                self.status_bar.success(f"Supplier found: {supplier['supplier_name']}")
        else:
            self._supplier = None
            self._sup_name.delete(0, "end")
            self._sup_addr.delete(0, "end")
            self._sup_gst.delete(0, "end")
            self._sup_status.config(text="New supplier — fill in details below",
                                     fg=THEME["warning"])

    def _add_to_cart(self):
        name = self._prod_name.get().strip()
        valid, msg = validate_not_empty(name, "Product Name")
        if not valid:
            messagebox.showwarning("Validation", msg)
            return

        valid, qty = validate_positive_int(self._prod_qty.get(), "Quantity")
        if not valid:
            messagebox.showwarning("Validation", qty)
            return

        valid, rate = validate_positive_decimal(self._prod_rate.get(), "Rate")
        if not valid:
            messagebox.showwarning("Validation", rate)
            return

        # Look up product — create if needed
        product = inventory_service.get_product_by_name(name)
        if not product:
            # Ask for product details
            if not self._ask_new_product(name, rate):
                return
            product = inventory_service.get_product_by_name(name)

        amount = qty * rate
        self._cart_counter += 1
        self._cart_items.append({
            "sno": self._cart_counter,
            "product_id": product["product_id"],
            "product_name": product["product_name"],
            "quantity": qty,
            "purchase_price": rate,
            "amount": amount,
            "unit": product.get("unit", "Pcs"),
        })
        self._refresh_cart()
        self._update_summary()

        # Clear inputs
        self._prod_name.delete(0, "end")
        self._prod_qty.delete(0, "end")
        self._prod_rate.delete(0, "end")
        self._prod_name.focus()

        if self.status_bar:
            self.status_bar.info(f"Added {name} × {qty}")

    def _ask_new_product(self, name, purchase_price):
        """Popup to create a new product."""
        dlg = tk.Toplevel(self)
        dlg.title("New Product")
        dlg.configure(bg=THEME["bg_card"])
        dlg.geometry("360x280")
        dlg.resizable(False, False)
        dlg.grab_set()

        result = {"ok": False}

        tk.Label(dlg, text=f"Product '{name}' not found.\nCreate it now:",
                 font=("Segoe UI", 10), fg=THEME["text_primary"],
                 bg=THEME["bg_card"], justify="left").pack(padx=16, pady=(14, 8))

        fields_frame = tk.Frame(dlg, bg=THEME["bg_card"])
        fields_frame.pack(fill="x", padx=16)

        # Category
        tk.Label(fields_frame, text="Category:", font=("Segoe UI", 9),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"]).grid(
            row=0, column=0, sticky="w", pady=4)
        categories = inventory_service.get_categories()
        cat_names = [c["category_name"] for c in categories]
        cat_combo = ttk.Combobox(fields_frame, values=cat_names, width=22)
        cat_combo.grid(row=0, column=1, pady=4, padx=(8, 0))
        if cat_names:
            cat_combo.current(0)

        # Unit
        tk.Label(fields_frame, text="Unit:", font=("Segoe UI", 9),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"]).grid(
            row=1, column=0, sticky="w", pady=4)
        unit_combo = ttk.Combobox(fields_frame, values=PRODUCT_UNITS, width=22)
        unit_combo.grid(row=1, column=1, pady=4, padx=(8, 0))
        unit_combo.current(0)

        # Selling Price
        tk.Label(fields_frame, text="Selling Price:", font=("Segoe UI", 9),
                 fg=THEME["text_secondary"], bg=THEME["bg_card"]).grid(
            row=2, column=0, sticky="w", pady=4)
        sell_price_entry = tk.Entry(fields_frame, font=("Segoe UI", 10),
                                     bg=THEME["entry_bg"], fg=THEME["entry_fg"],
                                     insertbackground=THEME["text_primary"],
                                     relief="flat", width=22)
        sell_price_entry.grid(row=2, column=1, pady=4, padx=(8, 0))

        def on_save():
            sp = sell_price_entry.get().strip()
            valid, sp_val = validate_positive_decimal(sp, "Selling Price")
            if not valid:
                messagebox.showwarning("Validation", sp_val, parent=dlg)
                return
            category = cat_combo.get().strip() or "Others"
            unit = unit_combo.get().strip() or "Pcs"

            inventory_service.create_product(
                name=name, category_name=category, unit=unit,
                selling_price=sp_val, purchase_price=purchase_price,
            )
            result["ok"] = True
            dlg.destroy()

        btn_frame = tk.Frame(dlg, bg=THEME["bg_card"])
        btn_frame.pack(pady=14)
        StyledButton(btn_frame, text="Create Product", command=on_save,
                     bg_color=THEME["success"], hover_color="#38e882",
                     font_size=10, padx=16, pady=6).pack(side="left", padx=4)
        StyledButton(btn_frame, text="Cancel", command=dlg.destroy,
                     bg_color=THEME["text_muted"], hover_color="#8888aa",
                     font_size=10, padx=16, pady=6).pack(side="left", padx=4)

        self.wait_window(dlg)
        return result["ok"]

    def _refresh_cart(self):
        self._cart_tree.delete(*self._cart_tree.get_children())
        for i, item in enumerate(self._cart_items):
            tag = "odd" if i % 2 == 0 else "even"
            self._cart_tree.insert("", "end", values=(
                item["sno"], item["product_name"], item["quantity"],
                f"₹{item['purchase_price']:,.2f}",
                f"₹{item['amount']:,.2f}",
            ), tags=(tag,))

    def _update_summary(self):
        subtotal = sum(item["amount"] for item in self._cart_items)
        try:
            discount = float(self._discount_entry.get() or 0)
        except ValueError:
            discount = 0
        grand_total = subtotal - discount
        self._subtotal_lbl.config(text=f"₹ {subtotal:,.2f}")
        self._grand_total_lbl.config(text=f"₹ {grand_total:,.2f}")

    def _remove_selected(self):
        sel = self._cart_tree.selection()
        if not sel:
            return
        idx = self._cart_tree.index(sel[0])
        self._cart_items.pop(idx)
        self._refresh_cart()
        self._update_summary()

    def _clear_cart(self):
        self._cart_items.clear()
        self._cart_counter = 0
        self._refresh_cart()
        self._update_summary()

    def _save_purchase(self):
        if not self._cart_items:
            messagebox.showwarning("Empty Cart", "Add at least one product.")
            return

        # Ensure supplier
        if not self._supplier:
            name = self._sup_name.get().strip()
            phone = self._sup_phone.get().strip()
            valid, phone_clean = validate_phone(phone)
            if not valid:
                messagebox.showwarning("Supplier", phone_clean)
                return
            v, msg = validate_not_empty(name, "Supplier Name")
            if not v:
                messagebox.showwarning("Supplier", msg)
                return
            addr = self._sup_addr.get().strip()
            gst = self._sup_gst.get().strip()
            sid = supplier_service.create_supplier(name, phone_clean, addr, gst)
            self._supplier = supplier_service.get_supplier(sid)

        try:
            discount = float(self._discount_entry.get() or 0)
        except ValueError:
            discount = 0

        notes = self._notes_entry.get().strip()

        try:
            result = purchase_service.save_purchase(
                supplier_id=self._supplier["supplier_id"],
                items=self._cart_items,
                discount=discount,
                notes=notes,
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save purchase:\n{e}")
            return

        # Generate PDF receipt
        try:
            purchase_data = purchase_service.get_purchase(result["purchase_id"])
            pdf_path = generate_purchase_receipt(
                purchase_data, purchase_data["items"], self._supplier
            )
            if self.status_bar:
                self.status_bar.success(
                    f"Purchase {result['purchase_number']} saved! PDF: {pdf_path}"
                )
        except Exception:
            if self.status_bar:
                self.status_bar.success(
                    f"Purchase {result['purchase_number']} saved! (PDF skipped)"
                )

        messagebox.showinfo(
            "Purchase Saved",
            f"Purchase Number: {result['purchase_number']}\n"
            f"Grand Total: ₹ {result['grand_total']:,.2f}\n\n"
            f"Stock has been updated automatically."
        )

        self._reset_form()

    def _reset_form(self):
        self._supplier = None
        self._cart_items.clear()
        self._cart_counter = 0
        self._sup_phone.delete(0, "end")
        self._sup_name.delete(0, "end")
        self._sup_addr.delete(0, "end")
        self._sup_gst.delete(0, "end")
        self._sup_status.config(text="")
        self._prod_name.delete(0, "end")
        self._prod_qty.delete(0, "end")
        self._prod_rate.delete(0, "end")
        self._discount_entry.delete(0, "end")
        self._discount_entry.insert(0, "0")
        self._notes_entry.delete(0, "end")
        self._refresh_cart()
        self._update_summary()
