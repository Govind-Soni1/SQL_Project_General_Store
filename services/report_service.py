# ==============================================================
# Report Service — dynamic report generation from live DB data
# ==============================================================

from database.db import fetch_one, fetch_all


# ======================== SALES REPORTS ==========================

def get_today_sales():
    """Today's total sales summary."""
    return fetch_one(
        "SELECT COUNT(*) AS total_bills, "
        "       COALESCE(SUM(grand_total), 0) AS total_revenue, "
        "       COALESCE(SUM(paid_amount), 0) AS total_collected, "
        "       COALESCE(SUM(due_amount), 0) AS total_due "
        "FROM sales WHERE DATE(sale_date) = CURDATE()"
    )


def get_today_sales_detail():
    """Detailed list of today's sales."""
    return fetch_all(
        "SELECT s.*, c.customer_name "
        "FROM sales s JOIN customer c ON s.customer_id = c.customer_id "
        "WHERE DATE(s.sale_date) = CURDATE() "
        "ORDER BY s.sale_date DESC"
    )


def get_monthly_sales(year, month):
    """Sales summary for a specific month."""
    return fetch_one(
        "SELECT COUNT(*) AS total_bills, "
        "       COALESCE(SUM(grand_total), 0) AS total_revenue, "
        "       COALESCE(SUM(paid_amount), 0) AS total_collected, "
        "       COALESCE(SUM(due_amount), 0) AS total_due "
        "FROM sales "
        "WHERE YEAR(sale_date) = %s AND MONTH(sale_date) = %s",
        (year, month),
    )


def get_monthly_sales_detail(year, month):
    """Detailed list of monthly sales."""
    return fetch_all(
        "SELECT s.*, c.customer_name "
        "FROM sales s JOIN customer c ON s.customer_id = c.customer_id "
        "WHERE YEAR(s.sale_date) = %s AND MONTH(s.sale_date) = %s "
        "ORDER BY s.sale_date DESC",
        (year, month),
    )


def get_yearly_sales(year):
    """Sales summary for a specific year."""
    return fetch_one(
        "SELECT COUNT(*) AS total_bills, "
        "       COALESCE(SUM(grand_total), 0) AS total_revenue, "
        "       COALESCE(SUM(paid_amount), 0) AS total_collected, "
        "       COALESCE(SUM(due_amount), 0) AS total_due "
        "FROM sales WHERE YEAR(sale_date) = %s",
        (year,),
    )


def get_yearly_sales_detail(year):
    """Monthly breakdown for a year."""
    return fetch_all(
        "SELECT MONTH(sale_date) AS month, "
        "       COUNT(*) AS total_bills, "
        "       COALESCE(SUM(grand_total), 0) AS total_revenue, "
        "       COALESCE(SUM(paid_amount), 0) AS total_collected, "
        "       COALESCE(SUM(due_amount), 0) AS total_due "
        "FROM sales WHERE YEAR(sale_date) = %s "
        "GROUP BY MONTH(sale_date) "
        "ORDER BY MONTH(sale_date)",
        (year,),
    )


# ======================== INVENTORY REPORTS ======================

def get_inventory_report():
    """Full inventory report with stock values."""
    return fetch_all(
        "SELECT p.product_id, p.product_name, c.category_name, p.unit, "
        "       p.stock, p.purchase_price, p.selling_price, "
        "       (p.stock * p.purchase_price) AS stock_cost_value, "
        "       (p.stock * p.selling_price) AS stock_sell_value, "
        "       p.reorder_level "
        "FROM product p "
        "LEFT JOIN category c ON p.category_id = c.category_id "
        "ORDER BY p.product_name"
    )


def get_low_stock_report():
    """Products at or below reorder level."""
    return fetch_all(
        "SELECT p.product_id, p.product_name, c.category_name, p.unit, "
        "       p.stock, p.reorder_level, "
        "       (p.reorder_level - p.stock) AS shortage "
        "FROM product p "
        "LEFT JOIN category c ON p.category_id = c.category_id "
        "WHERE p.stock <= p.reorder_level "
        "ORDER BY p.stock ASC"
    )


# ======================== PRODUCT REPORTS ========================

def get_best_selling_products(limit=20):
    """Top selling products by quantity sold."""
    return fetch_all(
        "SELECT p.product_id, p.product_name, c.category_name, "
        "       SUM(sd.quantity) AS total_qty_sold, "
        "       SUM(sd.amount) AS total_revenue "
        "FROM sale_details sd "
        "JOIN product p ON sd.product_id = p.product_id "
        "LEFT JOIN category c ON p.category_id = c.category_id "
        "GROUP BY sd.product_id "
        "ORDER BY total_qty_sold DESC "
        "LIMIT %s",
        (limit,),
    )


def get_product_profit_report():
    """Profit report per product: total sales revenue minus total purchase cost."""
    return fetch_all(
        "SELECT p.product_id, p.product_name, c.category_name, "
        "       COALESCE(sale_data.total_sold_qty, 0) AS total_sold_qty, "
        "       COALESCE(sale_data.total_sale_revenue, 0) AS total_sale_revenue, "
        "       COALESCE(purch_data.total_purchased_qty, 0) AS total_purchased_qty, "
        "       COALESCE(purch_data.total_purchase_cost, 0) AS total_purchase_cost, "
        "       (COALESCE(sale_data.total_sale_revenue, 0) - "
        "        COALESCE(purch_data.total_purchase_cost, 0)) AS profit "
        "FROM product p "
        "LEFT JOIN category c ON p.category_id = c.category_id "
        "LEFT JOIN ("
        "    SELECT product_id, SUM(quantity) AS total_sold_qty, "
        "           SUM(amount) AS total_sale_revenue "
        "    FROM sale_details GROUP BY product_id"
        ") sale_data ON p.product_id = sale_data.product_id "
        "LEFT JOIN ("
        "    SELECT product_id, SUM(quantity) AS total_purchased_qty, "
        "           SUM(amount) AS total_purchase_cost "
        "    FROM purchase_details GROUP BY product_id"
        ") purch_data ON p.product_id = purch_data.product_id "
        "ORDER BY profit DESC"
    )


# ======================== SUPPLIER / CUSTOMER ====================

def get_supplier_purchase_report():
    """Purchase totals grouped by supplier."""
    return fetch_all(
        "SELECT s.supplier_id, s.supplier_name, s.phone, "
        "       COUNT(p.purchase_id) AS total_purchases, "
        "       COALESCE(SUM(p.grand_total), 0) AS total_amount "
        "FROM supplier s "
        "LEFT JOIN purchase p ON s.supplier_id = p.supplier_id "
        "GROUP BY s.supplier_id "
        "ORDER BY total_amount DESC"
    )


def get_customer_purchase_report():
    """Sales totals grouped by customer."""
    return fetch_all(
        "SELECT c.customer_id, c.customer_name, c.phone, "
        "       COUNT(s.sale_id) AS total_bills, "
        "       COALESCE(SUM(s.grand_total), 0) AS total_amount, "
        "       COALESCE(SUM(s.due_amount), 0) AS total_due "
        "FROM customer c "
        "LEFT JOIN sales s ON c.customer_id = s.customer_id "
        "GROUP BY c.customer_id "
        "ORDER BY total_amount DESC"
    )


# ======================== OUTSTANDING DUES =======================

def get_outstanding_due_report():
    """All sales with outstanding dues."""
    return fetch_all(
        "SELECT s.sale_id, s.bill_number, s.sale_date, "
        "       c.customer_name, c.phone, "
        "       s.grand_total, s.paid_amount, s.due_amount "
        "FROM sales s "
        "JOIN customer c ON s.customer_id = c.customer_id "
        "WHERE s.due_amount > 0 "
        "ORDER BY s.due_amount DESC"
    )


def get_total_outstanding():
    """Total outstanding due across all customers."""
    row = fetch_one(
        "SELECT COALESCE(SUM(due_amount), 0) AS total "
        "FROM sales WHERE due_amount > 0"
    )
    return float(row["total"]) if row else 0.0


# ======================== DASHBOARD SUMMARY ======================

def get_dashboard_summary():
    """Quick summary data for the main dashboard."""
    today = get_today_sales()
    low_stock_count = fetch_one(
        "SELECT COUNT(*) AS cnt FROM product WHERE stock <= reorder_level"
    )
    total_products = fetch_one("SELECT COUNT(*) AS cnt FROM product")
    outstanding = get_total_outstanding()

    return {
        "today_sales": float(today["total_revenue"]) if today else 0.0,
        "today_bills": int(today["total_bills"]) if today else 0,
        "low_stock_count": int(low_stock_count["cnt"]) if low_stock_count else 0,
        "total_products": int(total_products["cnt"]) if total_products else 0,
        "outstanding_dues": outstanding,
    }
