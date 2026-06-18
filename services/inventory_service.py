# ==============================================================
# Inventory Service — read-only inventory views, product lookup
# ==============================================================

from database.db import execute_query, fetch_one, fetch_all
from config import DEFAULT_GST_RATE, DEFAULT_REORDER_LEVEL, DEFAULT_UNIT


def search_product(keyword):
    """Search products by name, barcode, or product_id.
    Returns a list of matching products.
    """
    like = f"%{keyword}%"
    # Try numeric ID match first
    try:
        pid = int(keyword)
        results = fetch_all(
            "SELECT p.*, c.category_name FROM product p "
            "LEFT JOIN category c ON p.category_id = c.category_id "
            "WHERE p.product_id = %s",
            (pid,),
        )
        if results:
            return results
    except (ValueError, TypeError):
        pass

    return fetch_all(
        "SELECT p.*, c.category_name FROM product p "
        "LEFT JOIN category c ON p.category_id = c.category_id "
        "WHERE p.product_name LIKE %s OR p.barcode LIKE %s "
        "ORDER BY p.product_name",
        (like, like),
    )


def get_product(product_id):
    """Get full product details by ID."""
    return fetch_one(
        "SELECT p.*, c.category_name FROM product p "
        "LEFT JOIN category c ON p.category_id = c.category_id "
        "WHERE p.product_id = %s",
        (product_id,),
    )


def get_product_by_name(name):
    """Get a product by exact name (case-insensitive)."""
    return fetch_one(
        "SELECT p.*, c.category_name FROM product p "
        "LEFT JOIN category c ON p.category_id = c.category_id "
        "WHERE LOWER(p.product_name) = LOWER(%s)",
        (name,),
    )


def get_all_products():
    """Return all products with category name."""
    return fetch_all(
        "SELECT p.*, c.category_name FROM product p "
        "LEFT JOIN category c ON p.category_id = c.category_id "
        "ORDER BY p.product_name"
    )


def get_low_stock_products():
    """Return products whose stock is at or below the reorder level."""
    return fetch_all(
        "SELECT p.*, c.category_name FROM product p "
        "LEFT JOIN category c ON p.category_id = c.category_id "
        "WHERE p.stock <= p.reorder_level "
        "ORDER BY p.stock ASC"
    )


def get_categories():
    """Return all categories."""
    return fetch_all("SELECT * FROM category ORDER BY category_name")


def get_or_create_category(category_name):
    """Find a category by name, or create it if it doesn't exist.
    Returns the category_id.
    """
    row = fetch_one(
        "SELECT category_id FROM category WHERE LOWER(category_name) = LOWER(%s)",
        (category_name,),
    )
    if row:
        return row["category_id"]
    return execute_query(
        "INSERT INTO category (category_name) VALUES (%s)",
        (category_name,),
    )


def create_product(name, category_name, unit=None, selling_price=0.0,
                   purchase_price=0.0, gst_rate=None, reorder_level=None,
                   barcode=None):
    """Create a new product.  Called automatically during purchase if product
    does not exist.  Returns the new product_id.
    """
    category_id = get_or_create_category(category_name)
    product_id = execute_query(
        "INSERT INTO product "
        "(product_name, category_id, unit, selling_price, purchase_price, "
        " gst_rate, reorder_level, barcode) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (
            name,
            category_id,
            unit or DEFAULT_UNIT,
            selling_price,
            purchase_price,
            gst_rate if gst_rate is not None else DEFAULT_GST_RATE,
            reorder_level if reorder_level is not None else DEFAULT_REORDER_LEVEL,
            barcode,
        ),
    )
    return product_id


def get_stock_transactions(product_id=None, limit=100):
    """Return stock transaction history.
    If product_id is given, filters to that product.
    """
    if product_id:
        return fetch_all(
            "SELECT st.*, p.product_name FROM stock_transaction st "
            "JOIN product p ON st.product_id = p.product_id "
            "WHERE st.product_id = %s ORDER BY st.txn_date DESC LIMIT %s",
            (product_id, limit),
        )
    return fetch_all(
        "SELECT st.*, p.product_name FROM stock_transaction st "
        "JOIN product p ON st.product_id = p.product_id "
        "ORDER BY st.txn_date DESC LIMIT %s",
        (limit,),
    )


def get_inventory_value():
    """Calculate total inventory value (stock × purchase_price)."""
    row = fetch_one(
        "SELECT COALESCE(SUM(stock * purchase_price), 0) AS total_value, "
        "       COALESCE(SUM(stock), 0) AS total_items, "
        "       COUNT(*) AS total_products "
        "FROM product"
    )
    return row
