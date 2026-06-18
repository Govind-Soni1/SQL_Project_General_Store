# ==============================================================
# Supplier Service — auto-lookup and creation
# ==============================================================

from database.db import execute_query, fetch_one, fetch_all


def find_by_phone(phone):
    """Look up a supplier by phone number.
    Returns a dict with supplier details or None.
    """
    return fetch_one(
        "SELECT * FROM supplier WHERE phone = %s", (phone,)
    )


def create_supplier(name, phone, address="", gst_number="", email=""):
    """Create a new supplier record and return the new supplier_id."""
    supplier_id = execute_query(
        "INSERT INTO supplier (supplier_name, phone, address, gst_number, email) "
        "VALUES (%s, %s, %s, %s, %s)",
        (name, phone, address, gst_number, email),
    )
    return supplier_id


def get_supplier(supplier_id):
    """Get a single supplier by ID."""
    return fetch_one(
        "SELECT * FROM supplier WHERE supplier_id = %s", (supplier_id,)
    )


def get_all_suppliers():
    """Return all suppliers ordered by name."""
    return fetch_all(
        "SELECT * FROM supplier ORDER BY supplier_name"
    )


def search_suppliers(keyword):
    """Search suppliers by name or phone."""
    like = f"%{keyword}%"
    return fetch_all(
        "SELECT * FROM supplier WHERE supplier_name LIKE %s OR phone LIKE %s",
        (like, like),
    )


def get_supplier_purchases(supplier_id):
    """Get all purchases from a specific supplier."""
    return fetch_all(
        "SELECT p.*, s.supplier_name "
        "FROM purchase p "
        "JOIN supplier s ON p.supplier_id = s.supplier_id "
        "WHERE p.supplier_id = %s "
        "ORDER BY p.purchase_date DESC",
        (supplier_id,),
    )


def get_supplier_purchase_total(supplier_id):
    """Get total purchase amount from a supplier."""
    row = fetch_one(
        "SELECT COALESCE(SUM(grand_total), 0) AS total "
        "FROM purchase WHERE supplier_id = %s",
        (supplier_id,),
    )
    return float(row["total"]) if row else 0.0
