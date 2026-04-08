"""
Seed database with test data
Run this after starting the app once
"""

from app import create_app, db
from app.models import Company, Warehouse, Product, Inventory, Supplier, SupplierProduct, SalesOrder
from datetime import datetime, timedelta
import random

app = create_app()

def seed_database():
    with app.app_context():
        print("🌱 Seeding database with test data...")
        
        # Clear existing data (be careful!)
        db.drop_all()
        db.create_all()
        
        # Create a test company
        company = Company(
            name="Test Retail Inc.",
            email="contact@testretail.com"
        )
        db.session.add(company)
        db.session.flush()
        
        # Create warehouses
        warehouses = [
            Warehouse(name="Main Warehouse", location="New York, NY", company_id=company.id),
            Warehouse(name="West Coast Hub", location="Los Angeles, CA", company_id=company.id),
            Warehouse(name="Central Distribution", location="Chicago, IL", company_id=company.id)
        ]
        
        for w in warehouses:
            db.session.add(w)
        db.session.flush()
        
        # Create suppliers
        suppliers = [
            Supplier(name="Global Supply Co.", contact_email="orders@globalsupply.com", contact_phone="555-0101"),
            Supplier(name="Premium Parts Ltd.", contact_email="sales@premiumparts.com", contact_phone="555-0102"),
            Supplier(name="Value Wholesalers", contact_email="info@valuewholesale.com", contact_phone="555-0103")
        ]
        
        for s in suppliers:
            db.session.add(s)
        db.session.flush()
        
        # Create products
        products_data = [
            {"name": "Widget A", "sku": "WID-001", "price": 29.99, "threshold": 20, "description": "Standard widget"},
            {"name": "Widget B", "sku": "WID-002", "price": 49.99, "threshold": 15, "description": "Premium widget"},
            {"name": "Gadget Pro", "sku": "GAD-001", "price": 99.99, "threshold": 10, "description": "Professional gadget"},
            {"name": "Accessory Kit", "sku": "ACC-001", "price": 19.99, "threshold": 25, "description": "Complete accessory set"},
            {"name": "Tool Set", "sku": "TOL-001", "price": 149.99, "threshold": 8, "description": "Deluxe tool set"}
        ]
        
        products = []
        for p_data in products_data:
            product = Product(
                name=p_data["name"],
                sku=p_data["sku"],
                price=p_data["price"],
                low_stock_threshold=p_data["threshold"],
                description=p_data["description"]
            )
            db.session.add(product)
            products.append(product)
        db.session.flush()
        
        # Link products to suppliers
        supplier_products = [
            (suppliers[0], products[0], "SUP-WID001", 5, 25.00, True),
            (suppliers[0], products[1], "SUP-WID002", 7, 42.00, True),
            (suppliers[1], products[2], "PP-GAD001", 10, 85.00, True),
            (suppliers[2], products[3], "VW-ACC001", 3, 15.00, True),
            (suppliers[0], products[4], "SUP-TOL001", 14, 120.00, True),
        ]
        
        for supplier, product, sup_sku, lead_time, cost, preferred in supplier_products:
            sp = SupplierProduct(
                supplier_id=supplier.id,
                product_id=product.id,
                supplier_sku=sup_sku,
                lead_time_days=lead_time,
                unit_cost=cost,
                is_preferred=preferred
            )
            db.session.add(sp)
        
        # Create inventory with some low stock items
        inventory_data = [
            # Main Warehouse
            (products[0], warehouses[0], 18),  # LOW (threshold 20)
            (products[1], warehouses[0], 45),  # OK
            (products[2], warehouses[0], 8),   # LOW (threshold 10)
            (products[3], warehouses[0], 30),  # OK
            (products[4], warehouses[0], 5),   # LOW (threshold 8)
            
            # West Coast Hub
            (products[0], warehouses[1], 22),  # LOW (threshold 20)
            (products[1], warehouses[1], 60),  # OK
            (products[2], warehouses[1], 12),  # OK
            (products[3], warehouses[1], 28),  # OK
            (products[4], warehouses[1], 9),   # OK
            
            # Central Distribution
            (products[0], warehouses[2], 15),  # LOW (threshold 20)
            (products[1], warehouses[2], 35),  # OK
            (products[2], warehouses[2], 6),   # LOW (threshold 10)
            (products[3], warehouses[2], 20),  # LOW (threshold 25)
            (products[4], warehouses[2], 7),   # LOW (threshold 8)
        ]
        
        for product, warehouse, quantity in inventory_data:
            inventory = Inventory(
                product_id=product.id,
                warehouse_id=warehouse.id,
                quantity=quantity
            )
            db.session.add(inventory)
        db.session.flush()
        
        # Create sales orders (last 30 days of activity)
        start_date = datetime.utcnow() - timedelta(days=30)
        
        for i in range(100):  # 100 sales transactions
            random_days = random.randint(0, 30)
            sale_date = start_date + timedelta(days=random_days)
            
            product = random.choice(products)
            warehouse = random.choice(warehouses)
            quantity = random.randint(1, 20)
            
            sale = SalesOrder(
                company_id=company.id,
                product_id=product.id,
                warehouse_id=warehouse.id,
                quantity_sold=quantity,
                sale_date=sale_date
            )
            db.session.add(sale)
        
        # Commit all data
        db.session.commit()
        
        print("✅ Database seeded successfully!")
        print("\n📊 Summary:")
        print(f"   - 1 Company created")
        print(f"   - {len(warehouses)} Warehouses created")
        print(f"   - {len(suppliers)} Suppliers created")
        print(f"   - {len(products)} Products created")
        print(f"   - {len(inventory_data)} Inventory records created")
        print(f"   - 100 Sales orders created")
        
        # Print low stock summary
        print("\n⚠️  Low Stock Items Created:")
        for product, warehouse, quantity in inventory_data:
            if quantity <= product.low_stock_threshold:
                print(f"   - {product.name} in {warehouse.name}: {quantity}/{product.low_stock_threshold}")

if __name__ == '__main__':
    seed_database()