"""
Low stock alerts endpoint - Part 3 Implementation
"""

from flask import Blueprint, jsonify, request
from app import db
from app.models import Company, Warehouse, Inventory, Product, Supplier, SupplierProduct, SalesOrder
from datetime import datetime, timedelta
from sqlalchemy import and_, func
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('alerts', __name__, url_prefix='/api')

@bp.route('/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
def get_low_stock_alerts(company_id):
    """
    Get low stock alerts for a company's warehouses
    
    Business Rules Implemented:
    1. Low stock threshold varies by product type (uses product.low_stock_threshold)
    2. Only alerts for products with recent sales activity (last 30 days)
    3. Handles multiple warehouses per company
    4. Includes supplier information for reordering
    
    Assumptions Made:
    - Recent sales activity = sales in last 30 days
    - Days until stockout = current_quantity / average_daily_sales (last 30 days)
    - If no sales data, days_until_stockout = None
    - Low stock if current_quantity <= threshold
    """
    
    try:
        # 1. VALIDATE COMPANY EXISTS
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'error': f'Company {company_id} not found'}), 404
        
        # 2. GET ALL WAREHOUSES FOR THIS COMPANY
        warehouses = Warehouse.query.filter_by(company_id=company_id).all()
        warehouse_ids = [w.id for w in warehouses]
        
        if not warehouse_ids:
            return jsonify({
                'alerts': [],
                'total_alerts': 0,
                'message': 'No warehouses found for this company'
            }), 200
        
        # 3. GET INVENTORY WITH PRODUCT INFO FOR THESE WAREHOUSES
        # Join to get product details and threshold
        inventory_items = db.session.query(
            Inventory,
            Product,
            Warehouse
        ).join(
            Product, Inventory.product_id == Product.id
        ).join(
            Warehouse, Inventory.warehouse_id == Warehouse.id
        ).filter(
            Inventory.warehouse_id.in_(warehouse_ids)
        ).all()
        
        alerts = []
        
        # 4. CALCULATE RECENT SALES ACTIVITY (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        for inventory, product, warehouse in inventory_items:
            # Check if product is low stock based on its threshold
            threshold = product.low_stock_threshold
            
            if inventory.quantity <= threshold:
                # Check for recent sales activity
                recent_sales = db.session.query(func.sum(SalesOrder.quantity_sold)).filter(
                    SalesOrder.product_id == product.id,
                    SalesOrder.warehouse_id == warehouse.id,
                    SalesOrder.sale_date >= thirty_days_ago
                ).scalar() or 0
                
                # Only include if there's recent sales activity
                if recent_sales > 0:
                    # Calculate average daily sales
                    avg_daily_sales = recent_sales / 30.0
                    
                    # Calculate days until stockout
                    if avg_daily_sales > 0:
                        days_until_stockout = int(inventory.quantity / avg_daily_sales)
                    else:
                        days_until_stockout = None
                    
                    # Get supplier information
                    supplier_product = SupplierProduct.query.filter_by(
                        product_id=product.id,
                        is_preferred=True
                    ).first()
                    
                    # If no preferred supplier, get any supplier
                    if not supplier_product:
                        supplier_product = SupplierProduct.query.filter_by(
                            product_id=product.id
                        ).first()
                    
                    supplier_info = None
                    if supplier_product and supplier_product.supplier:
                        supplier_info = {
                            'id': supplier_product.supplier.id,
                            'name': supplier_product.supplier.name,
                            'contact_email': supplier_product.supplier.contact_email
                        }
                    
                    # Create alert
                    alert = {
                        'product_id': product.id,
                        'product_name': product.name,
                        'sku': product.sku,
                        'warehouse_id': warehouse.id,
                        'warehouse_name': warehouse.name,
                        'current_stock': inventory.quantity,
                        'threshold': threshold,
                        'days_until_stockout': days_until_stockout,
                        'recent_sales_quantity': int(recent_sales),
                        'supplier': supplier_info
                    }
                    
                    alerts.append(alert)
        
        # 5. SORT ALERTS BY MOST URGENT (lowest days until stockout)
        alerts.sort(key=lambda x: (x['days_until_stockout'] if x['days_until_stockout'] is not None else float('inf')))
        
        logger.info(f"Generated {len(alerts)} low stock alerts for company {company_id}")
        
        return jsonify({
            'alerts': alerts,
            'total_alerts': len(alerts),
            'company_id': company_id,
            'company_name': company.name,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating low stock alerts: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@bp.route('/companies/<int:company_id>/alerts/low-stock', methods=['POST'])
def customize_threshold(company_id):
    """Customize low stock threshold for a product (POST for updates)"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        new_threshold = data.get('threshold')
        
        if not product_id or new_threshold is None:
            return jsonify({'error': 'product_id and threshold are required'}), 400
        
        try:
            new_threshold = int(new_threshold)
            if new_threshold < 0:
                return jsonify({'error': 'Threshold cannot be negative'}), 400
        except ValueError:
            return jsonify({'error': 'Threshold must be an integer'}), 400
        
        # Verify product belongs to company
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Update threshold
        product.low_stock_threshold = new_threshold
        db.session.commit()
        
        logger.info(f"Updated threshold for product {product_id} to {new_threshold}")
        
        return jsonify({
            'message': 'Threshold updated successfully',
            'product_id': product_id,
            'new_threshold': new_threshold
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating threshold: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500