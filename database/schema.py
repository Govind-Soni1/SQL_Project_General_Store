# ==============================================================
# Database Schema — CREATE TABLE statements & initialization
# ==============================================================

import mysql.connector
from config import DB_CONFIG, DEFAULT_CATEGORIES


def initialize_database():
    """Create the database and all tables if they don't exist.
    Seeds default categories on first run.
    """
    # --- Connect without specifying a database to create it ---
    conn = mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )
    cursor = conn.cursor()
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    conn.commit()
    cursor.close()
    conn.close()

    # --- Connect to the new database and create tables ---
    conn = mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
    )
    cursor = conn.cursor()

    tables = _get_table_definitions()
    for ddl in tables:
        cursor.execute(ddl)

    conn.commit()

    # --- Seed default categories if the table is empty ---
    cursor.execute("SELECT COUNT(*) FROM category")
    count = cursor.fetchone()[0]
    if count == 0:
        for cat in DEFAULT_CATEGORIES:
            cursor.execute(
                "INSERT INTO category (category_name) VALUES (%s)", (cat,)
            )
        conn.commit()

    cursor.close()
    conn.close()


def _get_table_definitions():
    """Return a list of CREATE TABLE DDL strings in dependency order."""
    return [
        # 1. category
        """
        CREATE TABLE IF NOT EXISTS category (
            category_id     INT AUTO_INCREMENT PRIMARY KEY,
            category_name   VARCHAR(100) NOT NULL UNIQUE,
            description     VARCHAR(255),
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """,

        # 2. product
        """
        CREATE TABLE IF NOT EXISTS product (
            product_id      INT AUTO_INCREMENT PRIMARY KEY,
            product_name    VARCHAR(150) NOT NULL,
            category_id     INT,
            unit            VARCHAR(30) DEFAULT 'Pcs',
            purchase_price  DECIMAL(10,2) DEFAULT 0.00,
            selling_price   DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            gst_rate        DECIMAL(5,2) DEFAULT 18.00,
            stock           INT DEFAULT 0,
            reorder_level   INT DEFAULT 10,
            barcode         VARCHAR(50) UNIQUE,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES category(category_id)
                ON UPDATE CASCADE ON DELETE SET NULL
        ) ENGINE=InnoDB;
        """,

        # 3. supplier
        """
        CREATE TABLE IF NOT EXISTS supplier (
            supplier_id     INT AUTO_INCREMENT PRIMARY KEY,
            supplier_name   VARCHAR(150) NOT NULL,
            phone           VARCHAR(15) NOT NULL UNIQUE,
            address         VARCHAR(255),
            gst_number      VARCHAR(20),
            email           VARCHAR(100),
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """,

        # 4. customer
        """
        CREATE TABLE IF NOT EXISTS customer (
            customer_id     INT AUTO_INCREMENT PRIMARY KEY,
            customer_name   VARCHAR(150) NOT NULL,
            phone           VARCHAR(15) NOT NULL UNIQUE,
            address         VARCHAR(255),
            email           VARCHAR(100),
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """,

        # 5. purchase
        """
        CREATE TABLE IF NOT EXISTS purchase (
            purchase_id     INT AUTO_INCREMENT PRIMARY KEY,
            purchase_number VARCHAR(30) NOT NULL UNIQUE,
            supplier_id     INT NOT NULL,
            purchase_date   DATETIME DEFAULT CURRENT_TIMESTAMP,
            subtotal        DECIMAL(12,2) DEFAULT 0.00,
            gst_amount      DECIMAL(12,2) DEFAULT 0.00,
            discount        DECIMAL(12,2) DEFAULT 0.00,
            grand_total     DECIMAL(12,2) DEFAULT 0.00,
            notes           VARCHAR(255),
            FOREIGN KEY (supplier_id) REFERENCES supplier(supplier_id)
                ON UPDATE CASCADE
        ) ENGINE=InnoDB;
        """,

        # 6. purchase_details
        """
        CREATE TABLE IF NOT EXISTS purchase_details (
            detail_id       INT AUTO_INCREMENT PRIMARY KEY,
            purchase_id     INT NOT NULL,
            product_id      INT NOT NULL,
            quantity        INT NOT NULL,
            purchase_price  DECIMAL(10,2) NOT NULL,
            amount          DECIMAL(12,2) NOT NULL,
            FOREIGN KEY (purchase_id) REFERENCES purchase(purchase_id)
                ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES product(product_id)
                ON UPDATE CASCADE
        ) ENGINE=InnoDB;
        """,

        # 7. sales
        """
        CREATE TABLE IF NOT EXISTS sales (
            sale_id         INT AUTO_INCREMENT PRIMARY KEY,
            bill_number     VARCHAR(30) NOT NULL UNIQUE,
            customer_id     INT NOT NULL,
            sale_date       DATETIME DEFAULT CURRENT_TIMESTAMP,
            subtotal        DECIMAL(12,2) DEFAULT 0.00,
            gst_amount      DECIMAL(12,2) DEFAULT 0.00,
            discount_pct    DECIMAL(5,2) DEFAULT 0.00,
            discount_amount DECIMAL(12,2) DEFAULT 0.00,
            grand_total     DECIMAL(12,2) DEFAULT 0.00,
            paid_amount     DECIMAL(12,2) DEFAULT 0.00,
            due_amount      DECIMAL(12,2) DEFAULT 0.00,
            payment_mode    VARCHAR(20) DEFAULT 'Cash',
            status          VARCHAR(20) DEFAULT 'Completed',
            FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
                ON UPDATE CASCADE
        ) ENGINE=InnoDB;
        """,

        # 8. sale_details
        """
        CREATE TABLE IF NOT EXISTS sale_details (
            detail_id       INT AUTO_INCREMENT PRIMARY KEY,
            sale_id         INT NOT NULL,
            product_id      INT NOT NULL,
            quantity        INT NOT NULL,
            selling_price   DECIMAL(10,2) NOT NULL,
            amount          DECIMAL(12,2) NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales(sale_id)
                ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES product(product_id)
                ON UPDATE CASCADE
        ) ENGINE=InnoDB;
        """,

        # 9. payment
        """
        CREATE TABLE IF NOT EXISTS payment (
            payment_id      INT AUTO_INCREMENT PRIMARY KEY,
            sale_id         INT NOT NULL,
            payment_date    DATETIME DEFAULT CURRENT_TIMESTAMP,
            amount          DECIMAL(12,2) NOT NULL,
            payment_mode    VARCHAR(20) NOT NULL,
            notes           VARCHAR(255),
            FOREIGN KEY (sale_id) REFERENCES sales(sale_id)
                ON UPDATE CASCADE
        ) ENGINE=InnoDB;
        """,

        # 10. stock_transaction
        """
        CREATE TABLE IF NOT EXISTS stock_transaction (
            txn_id          INT AUTO_INCREMENT PRIMARY KEY,
            product_id      INT NOT NULL,
            txn_type        VARCHAR(10) NOT NULL,
            quantity        INT NOT NULL,
            reference_type  VARCHAR(20),
            reference_id    INT,
            txn_date        DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes           VARCHAR(255),
            FOREIGN KEY (product_id) REFERENCES product(product_id)
                ON UPDATE CASCADE
        ) ENGINE=InnoDB;
        """,

        # 11. employee
        """
        CREATE TABLE IF NOT EXISTS employee (
            employee_id     INT AUTO_INCREMENT PRIMARY KEY,
            employee_name   VARCHAR(150) NOT NULL,
            phone           VARCHAR(15),
            role            VARCHAR(50) DEFAULT 'Cashier',
            address         VARCHAR(255),
            salary          DECIMAL(10,2),
            join_date       DATE,
            status          VARCHAR(20) DEFAULT 'Active',
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """,
    ]
