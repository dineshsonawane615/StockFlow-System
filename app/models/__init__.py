"""
Database Models for StockFlow
"""

from app import db
from datetime import datetime
from sqlalchemy import UniqueConstraint, CheckConstraint, Index

class Company(db.Model):
    """Company that uses the platform"""
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    warehouses = db.relationship('Warehouse', backref='company', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Warehouse(db.Model):
    """Physical warehouse location"""
    __tablename__ = 'warehouses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    inventory_items = db.relationship('Inventory', backref='warehouse', lazy=True, cascade='all, delete-orphan')
    
    # Composite unique constraint: company can't have duplicate warehouse names
    __table_args__ = (
        UniqueConstraint('company_id', 'name', name='uq_company_warehouse'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'company_id': self.company_id
        }

class Product(db.Model):
    """Product catalog"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)  # SKU must be globally unique
    price = db.Column(db.Numeric(10, 2), nullable=False)
    low_stock_threshold = db.Column(db.Integer, default=10)  # Default threshold
    is_bundle = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    inventory_items = db.relationship('Inventory', backref='product', lazy=True, cascade='all, delete-orphan')
    bundle_components = db.relationship('BundleComponent', backref='parent_product', 
                                        foreign_keys='BundleComponent.parent_product_id', lazy=True)
    supplier_products = db.relationship('SupplierProduct', backref='product', lazy=True)
    
    # Index for faster SKU lookup
    __table_args__ = (
        Index('idx_product_sku', 'sku'),
        CheckConstraint('price >= 0', name='check_positive_price'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'price': float(self.price) if self.price else None,
            'low_stock_threshold': self.low_stock_threshold,
            'is_bundle': self.is_bundle,
            'description': self.description
        }

class Inventory(db.Model):
    """Inventory levels for products in warehouses"""
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint: one product per warehouse
    __table_args__ = (
        UniqueConstraint('product_id', 'warehouse_id', name='uq_product_warehouse'),
        CheckConstraint('quantity >= 0', name='check_nonnegative_quantity'),
    )
    
    def to_dict(self):
        return {
            'product_id': self.product_id,
            'warehouse_id': self.warehouse_id,
            'quantity': self.quantity,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class InventoryTransaction(db.Model):
    """Track all inventory changes for audit"""
    __tablename__ = 'inventory_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    quantity_change = db.Column(db.Integer, nullable=False)  # Positive for addition, negative for removal
    previous_quantity = db.Column(db.Integer, nullable=False)
    new_quantity = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # 'stock_in', 'stock_out', 'adjustment'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    product = db.relationship('Product', backref='transactions')
    warehouse = db.relationship('Warehouse', backref='transactions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'warehouse_id': self.warehouse_id,
            'quantity_change': self.quantity_change,
            'previous_quantity': self.previous_quantity,
            'new_quantity': self.new_quantity,
            'transaction_type': self.transaction_type,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Supplier(db.Model):
    """Supplier information"""
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('SupplierProduct', backref='supplier', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'address': self.address
        }

class SupplierProduct(db.Model):
    """Link products to suppliers"""
    __tablename__ = 'supplier_products'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    supplier_sku = db.Column(db.String(50))  # Supplier's internal SKU
    lead_time_days = db.Column(db.Integer, default=7)
    unit_cost = db.Column(db.Numeric(10, 2))
    is_preferred = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint('supplier_id', 'product_id', name='uq_supplier_product'),
    )
    
    def to_dict(self):
        return {
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'product_id': self.product_id,
            'supplier_sku': self.supplier_sku,
            'lead_time_days': self.lead_time_days,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'is_preferred': self.is_preferred
        }

class BundleComponent(db.Model):
    """Products that make up a bundle"""
    __tablename__ = 'bundle_components'
    
    id = db.Column(db.Integer, primary_key=True)
    parent_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    component_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    # Relationships
    component = db.relationship('Product', foreign_keys=[component_product_id])
    
    __table_args__ = (
        UniqueConstraint('parent_product_id', 'component_product_id', name='uq_bundle_component'),
        CheckConstraint('quantity > 0', name='check_positive_quantity'),
    )

class SalesOrder(db.Model):
    """Track sales for recent activity calculation"""
    __tablename__ = 'sales_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Index for recent sales queries
    __table_args__ = (
        Index('idx_sales_recent', 'sale_date', 'product_id'),
    )