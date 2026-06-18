# ==============================================================
# General Store Management & Billing System
# Configuration File
# ==============================================================

import os

# ---- Load .env file if it exists (lightweight, no extra dependency) ----
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.isfile(_env_path):
    with open(_env_path, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                os.environ.setdefault(_key.strip(), _val.strip())

# ---------------------- MySQL Configuration -------------------
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "general_store"),
    "autocommit": False,
    "pool_name": "store_pool",
    "pool_size": 5,
}

# ---------------------- Store Information ---------------------
STORE_NAME = "My General Store"
STORE_ADDRESS = "123 Main Street, City, State - 000000"
STORE_PHONE = "+91 98765 43210"
STORE_GSTIN = "22AAAAA0000A1Z5"
STORE_EMAIL = "store@example.com"

# ---------------------- Business Defaults ---------------------
DEFAULT_GST_RATE = 18.0        # Default GST percentage
DEFAULT_REORDER_LEVEL = 10     # Low stock threshold
DEFAULT_UNIT = "Pcs"           # Default product unit

# ---------------------- Number Formats ------------------------
BILL_PREFIX = "BILL"
PURCHASE_PREFIX = "PUR"

# ---------------------- Report Output Directory ---------------
REPORTS_DIR = "reports"

# ---------------------- Supported Payment Modes ---------------
PAYMENT_MODES = ["Cash", "UPI", "Card", "Credit"]

# ---------------------- Product Units -------------------------
PRODUCT_UNITS = ["Pcs", "Kg", "Ltr", "Pack", "Box", "Dozen", "Meter", "Bundle"]

# ---------------------- Default Categories --------------------
DEFAULT_CATEGORIES = [
    "Grocery",
    "Dairy",
    "Beverages",
    "Snacks",
    "Personal Care",
    "Household",
    "Stationery",
    "Fruits & Vegetables",
    "Bakery",
    "Frozen Foods",
    "Others",
]

# ---------------------- UI Theme Colors -----------------------
THEME = {
    "bg_dark":       "#0f0f1a",
    "bg_medium":     "#1a1a2e",
    "bg_light":      "#16213e",
    "bg_card":       "#1f2940",
    "accent":        "#0f3460",
    "accent_hover":  "#1a4a7a",
    "primary":       "#e94560",
    "primary_hover": "#ff6b81",
    "success":       "#2ed573",
    "warning":       "#ffa502",
    "danger":        "#ff4757",
    "info":          "#1e90ff",
    "text_primary":  "#e0e0e0",
    "text_secondary":"#a0a0b0",
    "text_muted":    "#6c6c80",
    "border":        "#2a2a4a",
    "highlight":     "#533483",
    "treeview_odd":  "#1a1a2e",
    "treeview_even": "#1f2940",
    "entry_bg":      "#252545",
    "entry_fg":      "#e0e0e0",
    "button_bg":     "#0f3460",
    "button_fg":     "#e0e0e0",
}
