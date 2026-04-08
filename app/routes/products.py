"""
Product management routes - WITH FIXES FOR PART 1
"""

from flask import Blueprint, request, jsonify
from app import db
from app.models import Product, Inventory, Warehouse, InventoryTransaction
from sqlalchemy.exc import IntegrityError
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('products', __name__, url_prefix='/api')

@bp.route('/products', methods=['POST'])
def create_product():
    """
    FIXED VERSION - Addressing all issues from Part 1
    
    Issues Fixed:
    1. No validation for required fields
    2. No handling of optional fields
    3. No SKU uniqueness check
    4. No transaction rollback on failure
    5. No warehouse existence validation
    6. No error handling for invalid data types
    7. No logging for debugging
    8. Missing price validation (can't be negative)
    9. No response status codes
    10. Potential SQL injection (using parameterized queries - SQLAlchemy handles this)
    """
    
    try:
        # Get JSON data
        data = request.get_json()
        
        # 1. VALIDATE REQUIRED FIELDS
        required_fields = ['name', 'sku', 'price', 'warehouse_id']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        # 2. VALIDATE DATA TYPES AND VALUES
        try:
            price = float(data['price'])
            if price < 0:
                return jsonify({'error': 'Price cannot be negative'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Price must be a valid number'}), 400
        
        # Validate initial quantity (optional field)
        initial_quantity = data.get('initial_quantity', 0)
        try:
            initial_quantity = int(initial_quantity)
            if initial_quantity < 0:
                return jsonify({'error': 'Initial quantity cannot be negative'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Initial quantity must be a valid integer'}), 400
        
        # 3. CHECK IF WAREHOUSE EXISTS
        warehouse = Warehouse.query.get(data['warehouse_id'])
        if not warehouse:
            return jsonify({'error': f"Warehouse {data['warehouse_id']} not found"}), 404
        
        # 4. CHECK SKU UNIQUENESS
        existing_product = Product.query.filter_by(sku=data['sku']).first()
        if existing_product:
            return jsonify({'error': f"SKU '{data['sku']}' already exists"}), 409
        
        # 5. CREATE PRODUCT (with optional fields)
        product = Product(
            name=data['name'],
            sku=data['sku'],
            price=price,
            low_stock_threshold=data.get('low_stock_threshold', 10),  # Optional with default
            is_bundle=data.get('is_bundle', False),
            description=data.get('description')
        )
        
        db.session.add(product)
        db.session.flush()
        
        # 6. CREATE INVENTORY RECORD
        inventory = Inventory(
            product_id=product.id,  # This will be available after flush
            warehouse_id=data['warehouse_id'],
            quantity=initial_quantity
        )
        
        db.session.add(inventory)
        
        # 7. LOG THE TRANSACTION IF QUANTITY > 0
        if initial_quantity > 0:
            transaction = InventoryTransaction(
                product_id=product.id,
                warehouse_id=data['warehouse_id'],
                quantity_change=initial_quantity,
                previous_quantity=0,
                new_quantity=initial_quantity,
                transaction_type='stock_in',
                notes='Initial stock setup'
            )
            db.session.add(transaction)
        
        # 8. COMMIT ALL CHANGES (atomic operation)
        db.session.commit()
        
        # 9. LOG SUCCESS
        logger.info(f"Product created: ID={product.id}, SKU={product.sku}, Warehouse={data['warehouse_id']}")
        
        # 10. RETURN SUCCESS RESPONSE
        return jsonify({
            'message': 'Product created successfully',
            'product_id': product.id,
            'sku': product.sku,
            'initial_quantity': initial_quantity,
            'warehouse': warehouse.name
        }), 201
        
    except IntegrityError as e:
        # Handle database integrity errors
        db.session.rollback()
        logger.error(f"Database integrity error: {str(e)}")
        return jsonify({'error': 'Database constraint violation', 'details': str(e)}), 400
    
    except Exception as e:
        # Handle any other unexpected errors
        db.session.rollback()
        logger.error(f"Unexpected error creating product: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get product details including inventory across warehouses"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Get inventory across all warehouses
        inventory_items = Inventory.query.filter_by(product_id=product_id).all()
        
        result = product.to_dict()
        result['inventory'] = [
            {
                'warehouse_id': inv.warehouse_id,
                'warehouse_name': inv.warehouse.name,
                'quantity': inv.quantity
            }
            for inv in inventory_items
        ]
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error fetching product: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/products/<int:product_id>/inventory', methods=['PUT'])
def update_inventory(product_id):
    """Update inventory levels with transaction logging"""
    try:
        data = request.get_json()
        warehouse_id = data.get('warehouse_id')
        new_quantity = data.get('quantity')
        notes = data.get('notes', '')
        
        # Validate inputs
        if not warehouse_id or new_quantity is None:
            return jsonify({'error': 'warehouse_id and quantity are required'}), 400
        
        try:
            new_quantity = int(new_quantity)
            if new_quantity < 0:
                return jsonify({'error': 'Quantity cannot be negative'}), 400
        except ValueError:
            return jsonify({'error': 'Quantity must be an integer'}), 400
        
        # Find inventory record
        inventory = Inventory.query.filter_by(
            product_id=product_id,
            warehouse_id=warehouse_id
        ).first()
        
        if not inventory:
            return jsonify({'error': 'Inventory record not found'}), 404
        
        # Calculate change
        quantity_change = new_quantity - inventory.quantity
        previous_quantity = inventory.quantity
        
        # Update inventory
        inventory.quantity = new_quantity
        inventory.last_updated = db.func.current_timestamp()
        
        # Log transaction
        transaction = InventoryTransaction(
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity_change=quantity_change,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            transaction_type='adjustment',
            notes=notes
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        logger.info(f"Inventory updated: Product={product_id}, Warehouse={warehouse_id}, Change={quantity_change}")
        
        return jsonify({
            'message': 'Inventory updated successfully',
            'product_id': product_id,
            'warehouse_id': warehouse_id,
            'previous_quantity': previous_quantity,
            'new_quantity': new_quantity,
            'quantity_change': quantity_change
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating inventory: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500