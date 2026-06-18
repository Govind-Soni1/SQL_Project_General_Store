# 🏪 General Store Management & Billing System

A professional **Point-of-Sale (POS)** desktop application for small-to-medium retail stores built with **Python**, **MySQL**, and **Tkinter**. The system automates purchasing, sales, billing, inventory management, customer/supplier management, payment tracking, and reporting.

## ✨ Key Features

| Module | Highlights |
|---|---|
| **Sales / Billing** | Product search, GST calculation, discount %, Cash/UPI/Card/Credit payments, partial payment support |
| **Purchase Entry** | Supplier auto-lookup by phone, product cart, auto-create new products on the fly |
| **Inventory** | Read-only view, search by name/ID/barcode, low-stock alerts, Excel export |
| **Reports** | 10 dynamic reports (today/monthly/yearly sales, profit, best sellers, outstanding dues, etc.) |
| **Customer History** | Purchase history, outstanding dues, payment collection |
| **Supplier History** | Purchase history per supplier |
| **PDF Invoices** | Professional invoices generated via ReportLab |
| **Excel Export** | Styled exports for any report or inventory |
| **Backup / Restore** | Database backup & restore from the GUI |

## 🏗️ Architecture Principles

- **No manual DB operations** — All data flows through business operations (purchase, sell, view reports)
- **Atomic transactions** — Purchases and sales update stock, records, and logs in a single DB commit
- **Auto-lookup** — Suppliers and customers identified by phone number; auto-created if new
- **Stock integrity** — Stock only changes via purchase (+) and sale (-); no manual modification
- **Dynamic reports** — All reports computed from live data, never stored separately

## 📦 Tech Stack

- **Language:** Python 3.10+
- **Database:** MySQL 8.0+
- **GUI:** Tkinter with modern dark theme
- **PDF:** ReportLab
- **Excel:** openpyxl
- **Data:** pandas
- **DB Connector:** mysql-connector-python

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10 or higher
- MySQL 8.0 or higher (running)

### 1. Clone the repo
```bash
git clone https://github.com/Govind-Soni1/General_Store_Management_and_Bill_System.git
cd General_Store_Management_and_Bill_System
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure database credentials
```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your MySQL credentials
# DB_HOST=localhost
# DB_USER=root
# DB_PASSWORD=your_password
# DB_NAME=general_store
```

### 4. Run the application
```bash
python main.py
```

The database and all tables are created automatically on first run.

## 📁 Project Structure

```
General_Store_Management_and_Bill_System/
├── main.py                    # Application entry point
├── config.py                  # Configuration (reads from .env)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
│
├── database/
│   ├── db.py                  # Connection pool & query helpers
│   └── schema.py              # Table DDL & initialization
│
├── services/
│   ├── purchase_service.py    # Atomic purchase operations
│   ├── sales_service.py       # Atomic billing operations
│   ├── inventory_service.py   # Read-only inventory queries
│   ├── report_service.py      # Dynamic report generation
│   ├── customer_service.py    # Customer lookup & history
│   └── supplier_service.py    # Supplier lookup & history
│
├── screens/
│   ├── main_screen.py         # Dashboard with sidebar nav
│   ├── sales_screen.py        # Sales / billing UI
│   ├── purchase_screen.py     # Purchase entry UI
│   ├── inventory_screen.py    # Inventory view UI
│   ├── reports_screen.py      # Reports UI (10 reports)
│   ├── customer_history_screen.py
│   ├── supplier_history_screen.py
│   └── widgets.py             # Reusable custom widgets
│
├── utils/
│   ├── pdf_generator.py       # PDF invoice generation
│   ├── excel_export.py        # Excel export
│   ├── validators.py          # Input validation
│   └── backup.py              # DB backup & restore
│
└── reports/                   # Generated PDFs & Excel files
```

## 🗄️ Database Schema

11 tables with full relational integrity:

`category` → `product` → `purchase_details` / `sale_details` / `stock_transaction`

`supplier` → `purchase` → `purchase_details`

`customer` → `sales` → `sale_details` → `payment`

## 📊 Available Reports

1. Today's Sales
2. Monthly Sales
3. Yearly Sales
4. Inventory Report
5. Low Stock Report
6. Best Selling Products
7. Product Profit Report
8. Supplier Purchase Report
9. Customer Purchase History
10. Outstanding Due Report

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
