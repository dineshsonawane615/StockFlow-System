StockFlow - B2B Inventory Management System
Backend Engineering Case Study Documentation

Overview
StockFlow is a B2B inventory management platform. Small businesses use it to track products across multiple warehouses and manage supplier relationships.
Stack: Python | Flask | MySQL | SQLAlchemy | Flask-Migrate

Quick Start
bash# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt
pip install PyMySQL

# 3. Create MySQL database
# Run in MySQL Workbench:
# CREATE DATABASE stockflow_db;

# 4. Set your database URL in app/.env
# DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/stockflow_db

# 5. Run migrations
flask db init
flask db migrate -m "initial"
flask db upgrade

# 6. Seed test data
python seed_data.py

# 7. Start server
python run.py
# Runs at http://localhost:5000

Part 1: Code Review & Debugging
Issues Found in Original Code
1. No Input Validation

Issue: Input data was not validated. App crashes with KeyError if any field is missing.
Solution: Added checks for all required fields (name, sku, price, warehouse_id), data types, and value ranges.
Implementation: Validate required fields list before any DB operation.

2. SKU Not Unique

Issue: Duplicate SKUs were allowed, breaking order fulfillment logic.
Solution: Query database before insert to check SKU uniqueness.
Implementation: Return 409 Conflict if SKU already exists.

3. Multiple Commits (Data Inconsistency)

Issue: Two separate db.session.commit() calls — if inventory insert fails, product is saved without stock.
Solution: Single atomic transaction using db.session.flush() then one db.session.commit().
Implementation: Full try/except block with db.session.rollback() on any error.

4. No Warehouse Validation

Issue: Inventory linked to a warehouse that may not exist.
Solution: Check warehouse exists before creating any records.
Implementation: Return 404 Not Found if warehouse missing.

5. No Price Validation

Issue: Negative prices could be stored.
Solution: Validate price >= 0 and that it is a valid number.
Implementation: float() conversion with value check.

6. No Error Handling

Issue: Any unexpected error returns a raw 500 with no useful message.
Solution: try/except with proper HTTP status codes and error messages.
Implementation: 400, 404, 409, 500 responses with JSON body.

7. No Logging

Issue: Impossible to debug production issues.
Solution: Added logger.info on success and logger.error on failure.

8. No Initial Quantity Validation

Issue: Negative or non-integer initial quantity could be stored.
Solution: Validate initial_quantity is a non-negative integer (default: 0).


Part 2: Database Design
Schema
1. Company
ColumnTypeNotesidINTPrimary KeynameVARCHAR(200)Not nullemailVARCHAR(120)Unique, not nullcreated_atDATETIMEAuto
One Company → Many Warehouses
2. Warehouse
ColumnTypeNotesidINTPrimary KeynameVARCHAR(100)Not nulllocationVARCHAR(200)company_idINTFK → companies.idcreated_atDATETIMEAuto
Unique constraint: (company_id, name) — company cannot have duplicate warehouse names.
3. Product
ColumnTypeNotesidINTPrimary KeynameVARCHAR(200)Not nullskuVARCHAR(50)Globally uniquepriceDECIMAL(10,2)>= 0low_stock_thresholdINTDefault: 10is_bundleBOOLEANDefault: falsedescriptionTEXTOptionalcreated_atDATETIMEAuto
Index on sku for fast lookup.
4. Inventory
ColumnTypeNotesidINTPrimary Keyproduct_idINTFK → products.idwarehouse_idINTFK → warehouses.idquantityINT>= 0last_updatedDATETIMEAuto-update
Unique constraint: (product_id, warehouse_id) — one record per product per warehouse.
5. Inventory Transaction
ColumnTypeNotesidINTPrimary Keyproduct_idINTFK → products.idwarehouse_idINTFK → warehouses.idquantity_changeINTPositive or negativeprevious_quantityINTnew_quantityINTtransaction_typeVARCHAR(50)stock_in / stock_out / adjustmentnotesTEXTOptionalcreated_atDATETIMEIndexed
Immutable audit log — never updated, only inserted.
6. Sales Orders
ColumnTypeNotesidINTPrimary Keycompany_idINTFK → companies.idproduct_idINTFK → products.idwarehouse_idINTFK → warehouses.idquantity_soldINTsale_dateDATETIMEIndexed
Used for stockout prediction (days_until_stockout calculation).
7. Supplier
ColumnTypeNotesidINTPrimary KeynameVARCHAR(200)contact_emailVARCHAR(120)contact_phoneVARCHAR(20)addressTEXTcreated_atDATETIME
8. Supplier Product
ColumnTypeNotesidINTPrimary Keysupplier_idINTFK → suppliers.idproduct_idINTFK → products.idsupplier_skuVARCHAR(50)Supplier's internal SKUlead_time_daysINTDefault: 7unit_costDECIMAL(10,2)is_preferredBOOLEANDefault: false
Many-to-Many relationship between suppliers and products.
9. Bundle Components
ColumnTypeNotesidINTPrimary Keyparent_product_idINTFK → products.idcomponent_product_idINTFK → products.idquantityINT> 0
Self-referencing relationship for bundle products.
Design Decisions

Inventory table is separate from Products — allows one product in many warehouses with independent quantities
All constraints enforced at DB level (UniqueConstraint, CheckConstraint), not just application layer
is_preferred flag on SupplierProduct — alerts endpoint picks preferred supplier first for reorder info
sale_date indexed on sales_orders — efficient 30-day window queries for stockout prediction

Gaps / Questions for Product Team

Can a product belong to multiple companies, or is it always global?
Should bundles also track inventory, or derive it from components?
What defines "recent sales activity" — is 30 days the right window?
Do we need user/auth tables, or is this API always server-to-server?


Part 3: API Implementation
Endpoints
POST /api/products — Create Product
json{
  "name": "Widget A",
  "sku": "WID-001",
  "price": 29.99,
  "warehouse_id": 1,
  "initial_quantity": 50,
  "low_stock_threshold": 20,
  "is_bundle": false,
  "description": "Standard widget"
}
Required: name, sku, price, warehouse_id
GET /api/products/<id> — Get Product
Returns product details with inventory across all warehouses.
PUT /api/products/<id>/inventory — Update Inventory
json{
  "warehouse_id": 1,
  "quantity": 75,
  "notes": "Restocked from supplier"
}
GET /api/companies/<company_id>/alerts/low-stock — Low Stock Alerts
Business Rules:

Low stock: current_quantity <= product.low_stock_threshold
Only alerts for products with sales in last 30 days
Handles multiple warehouses per company
Includes preferred supplier info for reordering
days_until_stockout = current_quantity / avg_daily_sales (30 days)
Sorted by most urgent (lowest days_until_stockout first)

Response:
json{
  "alerts": [
    {
      "product_id": 1,
      "product_name": "Widget A",
      "sku": "WID-001",
      "warehouse_id": 1,
      "warehouse_name": "Pune Warehouse",
      "current_stock": 5,
      "threshold": 20,
      "days_until_stockout": 12,
      "recent_sales_quantity": 30,
      "supplier": {
        "id": 1,
        "name": "Global Supply Co.",
        "contact_email": "orders@globalsupply.com"
      }
    }
  ],
  "total_alerts": 1,
  "company_id": 1,
  "company_name": "Dinesh Enterprises"
}
Edge Cases Handled:

Company not found → 404
No warehouses for company → empty alerts, 200
No recent sales → product excluded from alerts
No preferred supplier → fallback to any supplier, null if none
avg_daily_sales = 0 → days_until_stockout set to null (no divide-by-zero)
DB error → 500 with error details

POST /api/companies/<company_id>/alerts/low-stock — Update Threshold
json{
  "product_id": 1,
  "threshold": 25
}

Project Structure
stockflow-system/
├── app/
│   ├── __init__.py          # App factory, DB and migration init
│   ├── models/
│   │   └── __init__.py      # All SQLAlchemy models (9 tables)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── products.py      # Product & inventory endpoints
│   │   └── alerts.py        # Low stock alert endpoints
│   └── .env                 # Environment config
├── run.py                   # Entry point
├── seed_data.py             # Test data seeder
├── test_api.py              # API tests
├── requirements.txt
└── README.md

Assumptions Made

Recent sales activity = SalesOrder records within last 30 days
Low stock condition: inventory.quantity <= product.low_stock_threshold
Preferred supplier identified by is_preferred=True on SupplierProduct
days_until_stockout is rounded down to integer
All warehouses of the company are checked for alerts