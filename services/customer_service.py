# ==============================================================
# Customer Service — auto-lookup, creation, and history
# ==============================================================

from database.db import execute_query, fetch_one, fetch_all


def find_by_phone(phone):
    """Look up a customer by phone number.
    Returns a dict with customer details or None.
    """
    return fetch_one(
        "SELECT * FROM customer WHERE phone = %s", (phone,)
    )


def create_customer(name, phone, address="", email=""):
    """Create a new customer record and return the new customer_id."""
    customer_id = execute_query(
        "INSERT INTO customer (customer_name, phone, address, email) "
        "VALUES (%s, %s, %s, %s)",
        (name, phone, address, email),
    )
    return customer_id


def get_customer(customer_id):
    """Get a single customer by ID."""
    return fetch_one(
        "SELECT * FROM customer WHERE customer_id = %s", (customer_id,)
    )


def get_all_customers():
    """Return all customers ordered by name."""
    return fetch_all(
        "SELECT * FROM customer ORDER BY customer_name"
    )


def search_customers(keyword):
    """Search customers by name or phone."""
    like = f"%{keyword}%"
    return fetch_all(
        "SELECT * FROM customer WHERE customer_name LIKE %s OR phone LIKE %s",
        (like, like),
    )


def get_customer_history(customer_id):
    """Get all sales for a specific customer."""
    return fetch_all(
        "SELECT * FROM sales WHERE customer_id = %s ORDER BY sale_date DESC",
        (customer_id,),
    )


def get_outstanding_dues(customer_id=None):
    """Get sales with outstanding dues.
    If customer_id is None, returns all outstanding dues.
    """
    if customer_id:
        return fetch_all(
            "SELECT s.*, c.customer_name, c.phone "
            "FROM sales s JOIN customer c ON s.customer_id = c.customer_id "
            "WHERE s.due_amount > 0 AND s.customer_id = %s "
            "ORDER BY s.sale_date DESC",
            (customer_id,),
        )
    return fetch_all(
        "SELECT s.*, c.customer_name, c.phone "
        "FROM sales s JOIN customer c ON s.customer_id = c.customer_id "
        "WHERE s.due_amount > 0 "
        "ORDER BY s.sale_date DESC"
    )


def get_customer_total_spent(customer_id):
    """Get total amount spent by a customer."""
    row = fetch_one(
        "SELECT COALESCE(SUM(grand_total), 0) AS total "
        "FROM sales WHERE customer_id = %s",
        (customer_id,),
    )
    return float(row["total"]) if row else 0.0


def get_customer_total_due(customer_id):
    """Get total outstanding due for a customer."""
    row = fetch_one(
        "SELECT COALESCE(SUM(due_amount), 0) AS total_due "
        "FROM sales WHERE customer_id = %s AND due_amount > 0",
        (customer_id,),
    )
    return float(row["total_due"]) if row else 0.0
