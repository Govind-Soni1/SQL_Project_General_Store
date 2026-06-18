# ==============================================================
# Database Connection Layer — connection pool & query helpers
# ==============================================================

import mysql.connector
from mysql.connector import pooling, Error as MySQLError
from config import DB_CONFIG


_pool = None


def _get_pool():
    """Lazily create and return the connection pool."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name=DB_CONFIG.get("pool_name", "store_pool"),
            pool_size=DB_CONFIG.get("pool_size", 5),
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            autocommit=False,
        )
    return _pool


def get_connection():
    """Get a connection from the pool."""
    return _get_pool().get_connection()


def execute_query(query, params=None):
    """Execute an INSERT / UPDATE / DELETE and commit.
    Returns the lastrowid for INSERT statements.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id
    except MySQLError:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_one(query, params=None):
    """Execute a SELECT and return a single row as a dict, or None."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        row = cursor.fetchone()
        cursor.close()
        return row
    finally:
        conn.close()


def fetch_all(query, params=None):
    """Execute a SELECT and return all rows as a list of dicts."""
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()


def execute_transaction(operations):
    """Execute multiple (query, params) tuples in a single transaction.

    Parameters
    ----------
    operations : list[tuple[str, tuple|None]]
        Each element is (sql_string, params_tuple).

    Returns
    -------
    list[int]
        List of lastrowid values for each operation.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        results = []
        for query, params in operations:
            cursor.execute(query, params or ())
            results.append(cursor.lastrowid)
        conn.commit()
        cursor.close()
        return results
    except MySQLError:
        conn.rollback()
        raise
    finally:
        conn.close()
