# ==============================================================
# Purchase Service — record purchases & auto-update inventory
# ==============================================================

from datetime import datetime
from database.db import get_connection, fetch_one, fetch_all
from mysql.connector import Error as MySQLError


def generate_purchase_number():
    """Generate the next purchase number in format PUR-YYYY-NNNNNN."""
    year = datetime.now().year
    prefix = f"PUR-{year}-"
    row = fetch_one(
        "SELECT purchase_number FROM purchase "
        "WHERE purchase_number LIKE %s "
        "ORDER BY purchase_id DESC LIMIT 1",
        (f"{prefix}%",),
    )
    if row:
        last_num = int(row["purchase_number"].split("-")[-1])
        next_num = last_num + 1
    else:
        next_num = 1
    return f"{prefix}{next_num:06d}"


def save_purchase(supplier_id, items, discount=0.0, notes=""):
    """Save a complete purchase as an atomic transaction.

    Parameters
    ----------
    supplier_id : int
    items : list[dict]
        Each dict: {product_id, product_name, quantity, purchase_price}
    discount : float
        Flat discount amount on the total.
    notes : str

    Returns
    -------
    dict  with purchase_id, purchase_number, grand_total

    The transaction atomically:
    1. Inserts the purchase header
    2. Inserts purchase_details rows
    3. Updates product stock (+=qty) and purchase_price
    4. Inserts stock_transaction records (type='IN')
    """
    purchase_number = generate_purchase_number()

    # Calculate totals
    subtotal = sum(item["quantity"] * item["purchase_price"] for item in items)
    grand_total = subtotal - discount

    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 1. Insert purchase header
        cursor.execute(
            "INSERT INTO purchase "
            "(purchase_number, supplier_id, subtotal, discount, grand_total, notes) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (purchase_number, supplier_id, subtotal, discount, grand_total, notes),
        )
        purchase_id = cursor.lastrowid

        # 2-4. For each item: insert detail, update stock, log transaction
        for item in items:
            amount = item["quantity"] * item["purchase_price"]

            # Insert purchase detail
            cursor.execute(
                "INSERT INTO purchase_details "
                "(purchase_id, product_id, quantity, purchase_price, amount) "
                "VALUES (%s, %s, %s, %s, %s)",
                (purchase_id, item["product_id"], item["quantity"],
                 item["purchase_price"], amount),
            )

            # Update product stock and latest purchase price
            cursor.execute(
                "UPDATE product SET stock = stock + %s, purchase_price = %s, "
                "updated_at = NOW() WHERE product_id = %s",
                (item["quantity"], item["purchase_price"], item["product_id"]),
            )

            # Insert stock transaction
            cursor.execute(
                "INSERT INTO stock_transaction "
                "(product_id, txn_type, quantity, reference_type, reference_id, notes) "
                "VALUES (%s, 'IN', %s, 'PURCHASE', %s, %s)",
                (item["product_id"], item["quantity"], purchase_id,
                 f"Purchase {purchase_number}"),
            )

        conn.commit()
        cursor.close()

        return {
            "purchase_id": purchase_id,
            "purchase_number": purchase_number,
            "subtotal": subtotal,
            "discount": discount,
            "grand_total": grand_total,
        }

    except MySQLError:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_purchase(purchase_id):
    """Get a purchase header with its details."""
    header = fetch_one(
        "SELECT p.*, s.supplier_name, s.phone AS supplier_phone "
        "FROM purchase p "
        "JOIN supplier s ON p.supplier_id = s.supplier_id "
        "WHERE p.purchase_id = %s",
        (purchase_id,),
    )
    if not header:
        return None
    details = fetch_all(
        "SELECT pd.*, pr.product_name, pr.unit "
        "FROM purchase_details pd "
        "JOIN product pr ON pd.product_id = pr.product_id "
        "WHERE pd.purchase_id = %s",
        (purchase_id,),
    )
    header["items"] = details
    return header


def get_all_purchases(date_from=None, date_to=None):
    """Get all purchases, optionally filtered by date range."""
    query = (
        "SELECT p.*, s.supplier_name "
        "FROM purchase p "
        "JOIN supplier s ON p.supplier_id = s.supplier_id "
    )
    params = []
    conditions = []
    if date_from:
        conditions.append("p.purchase_date >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("p.purchase_date <= %s")
        params.append(date_to)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY p.purchase_date DESC"
    return fetch_all(query, tuple(params))
