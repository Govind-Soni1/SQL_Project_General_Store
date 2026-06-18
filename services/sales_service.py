# ==============================================================
# Sales / Billing Service — generate bills & auto-update inventory
# ==============================================================

from datetime import datetime
from database.db import get_connection, fetch_one, fetch_all, execute_query
from mysql.connector import Error as MySQLError


def generate_bill_number():
    """Generate the next bill number in format BILL-YYYY-NNNNNN."""
    year = datetime.now().year
    prefix = f"BILL-{year}-"
    row = fetch_one(
        "SELECT bill_number FROM sales "
        "WHERE bill_number LIKE %s "
        "ORDER BY sale_id DESC LIMIT 1",
        (f"{prefix}%",),
    )
    if row:
        last_num = int(row["bill_number"].split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    return f"{prefix}{next_num:06d}"


class InsufficientStockError(Exception):
    """Raised when sale quantity exceeds available stock."""
    pass


def save_sale(customer_id, items, discount_pct=0.0, paid_amount=0.0,
              payment_mode="Cash"):
    """Save a complete sale/bill as an atomic transaction.

    Parameters
    ----------
    customer_id : int
    items : list[dict]
        Each dict: {product_id, product_name, quantity, selling_price, stock}
    discount_pct : float
        Discount percentage on subtotal.
    paid_amount : float
    payment_mode : str  (Cash / UPI / Card / Credit)

    Returns
    -------
    dict  with sale_id, bill_number, grand_total, due_amount, etc.

    Raises
    ------
    InsufficientStockError  if any item quantity > available stock.

    The transaction atomically:
    1. Validates stock availability
    2. Inserts the sales header
    3. Inserts sale_details rows
    4. Updates product stock (-=qty)
    5. Inserts stock_transaction records (type='OUT')
    6. Inserts payment record
    """
    bill_number = generate_bill_number()

    # Pre-validate stock
    for item in items:
        if item["quantity"] > item.get("stock", 0):
            raise InsufficientStockError(
                f"Insufficient stock for '{item['product_name']}'. "
                f"Available: {item.get('stock', 0)}, Requested: {item['quantity']}"
            )

    # Calculate totals
    subtotal = sum(item["quantity"] * item["selling_price"] for item in items)
    discount_amount = round(subtotal * discount_pct / 100, 2)
    after_discount = subtotal - discount_amount

    # Calculate GST on each item based on its rate
    gst_amount = 0.0
    for item in items:
        item_total = item["quantity"] * item["selling_price"]
        gst_rate = item.get("gst_rate", 18.0)
        gst_amount += round(item_total * gst_rate / 100, 2)

    grand_total = round(after_discount + gst_amount, 2)
    due_amount = round(grand_total - paid_amount, 2)
    if due_amount < 0:
        due_amount = 0.0

    status = "Completed"
    if due_amount > 0 and paid_amount > 0:
        status = "Partial"
    elif due_amount > 0 and paid_amount == 0:
        status = "Credit"

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 1. Insert sales header
        cursor.execute(
            "INSERT INTO sales "
            "(bill_number, customer_id, subtotal, gst_amount, discount_pct, "
            " discount_amount, grand_total, paid_amount, due_amount, "
            " payment_mode, status) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (bill_number, customer_id, subtotal, gst_amount, discount_pct,
             discount_amount, grand_total, paid_amount, due_amount,
             payment_mode, status),
        )
        sale_id = cursor.lastrowid

        # 2-5. For each item
        for item in items:
            amount = item["quantity"] * item["selling_price"]

            # Insert sale detail
            cursor.execute(
                "INSERT INTO sale_details "
                "(sale_id, product_id, quantity, selling_price, amount) "
                "VALUES (%s, %s, %s, %s, %s)",
                (sale_id, item["product_id"], item["quantity"],
                 item["selling_price"], amount),
            )

            # Update product stock
            cursor.execute(
                "UPDATE product SET stock = stock - %s, updated_at = NOW() "
                "WHERE product_id = %s",
                (item["quantity"], item["product_id"]),
            )

            # Insert stock transaction
            cursor.execute(
                "INSERT INTO stock_transaction "
                "(product_id, txn_type, quantity, reference_type, reference_id, notes) "
                "VALUES (%s, 'OUT', %s, 'SALE', %s, %s)",
                (item["product_id"], item["quantity"], sale_id,
                 f"Bill {bill_number}"),
            )

        # 6. Insert payment record (if amount paid > 0)
        if paid_amount > 0:
            cursor.execute(
                "INSERT INTO payment (sale_id, amount, payment_mode, notes) "
                "VALUES (%s, %s, %s, %s)",
                (sale_id, paid_amount, payment_mode, f"Payment for {bill_number}"),
            )

        conn.commit()
        cursor.close()

        return {
            "sale_id": sale_id,
            "bill_number": bill_number,
            "subtotal": subtotal,
            "gst_amount": gst_amount,
            "discount_pct": discount_pct,
            "discount_amount": discount_amount,
            "grand_total": grand_total,
            "paid_amount": paid_amount,
            "due_amount": due_amount,
            "payment_mode": payment_mode,
            "status": status,
        }

    except MySQLError:
        conn.rollback()
        raise
    finally:
        conn.close()


def record_due_payment(sale_id, amount, payment_mode="Cash"):
    """Record a payment against an outstanding due.
    Updates the sales record and creates a payment record.
    """
    sale = fetch_one("SELECT * FROM sales WHERE sale_id = %s", (sale_id,))
    if not sale:
        raise ValueError(f"Sale {sale_id} not found")

    current_due = float(sale["due_amount"])
    if amount > current_due:
        amount = current_due  # Cap at due amount

    new_paid = float(sale["paid_amount"]) + amount
    new_due = round(current_due - amount, 2)
    new_status = "Completed" if new_due <= 0 else "Partial"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sales SET paid_amount = %s, due_amount = %s, status = %s "
            "WHERE sale_id = %s",
            (new_paid, new_due, new_status, sale_id),
        )
        cursor.execute(
            "INSERT INTO payment (sale_id, amount, payment_mode, notes) "
            "VALUES (%s, %s, %s, %s)",
            (sale_id, amount, payment_mode,
             f"Due payment for {sale['bill_number']}"),
        )
        conn.commit()
        cursor.close()
        return {"new_paid": new_paid, "new_due": new_due, "status": new_status}
    except MySQLError:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_sale(sale_id):
    """Get a sale header with its details."""
    header = fetch_one(
        "SELECT s.*, c.customer_name, c.phone AS customer_phone, c.address AS customer_address "
        "FROM sales s "
        "JOIN customer c ON s.customer_id = c.customer_id "
        "WHERE s.sale_id = %s",
        (sale_id,),
    )
    if not header:
        return None
    details = fetch_all(
        "SELECT sd.*, p.product_name, p.unit "
        "FROM sale_details sd "
        "JOIN product p ON sd.product_id = p.product_id "
        "WHERE sd.sale_id = %s",
        (sale_id,),
    )
    header["items"] = details
    payments = fetch_all(
        "SELECT * FROM payment WHERE sale_id = %s ORDER BY payment_date",
        (sale_id,),
    )
    header["payments"] = payments
    return header


def get_all_sales(date_from=None, date_to=None):
    """Get all sales, optionally filtered by date range."""
    query = (
        "SELECT s.*, c.customer_name "
        "FROM sales s "
        "JOIN customer c ON s.customer_id = c.customer_id "
    )
    params = []
    conditions = []
    if date_from:
        conditions.append("s.sale_date >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("s.sale_date <= %s")
        params.append(date_to)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY s.sale_date DESC"
    return fetch_all(query, tuple(params))
