"""
Test script for StockFlow API
Run after starting the server
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_create_product():
    """Test product creation endpoint"""
    print("\n📝 Testing POST /products")
    
    # Test 1: Valid product creation
    product_data = {
        "name": "Test Widget",
        "sku": "TEST-001",
        "price": 39.99,
        "warehouse_id": 1,
        "initial_quantity": 50,
        "description": "A test product"
    }
    
    response = requests.post(f"{BASE_URL}/products", json=product_data)
    print(f"  Valid product: {response.status_code}")
    if response.status_code == 201:
        print(f"    Response: {response.json()}")
    
    # Test 2: Missing required field
    invalid_data = {
        "name": "Bad Product",
        "price": 10.00
    }
    response = requests.post(f"{BASE_URL}/products", json=invalid_data)
    print(f"  Missing fields: {response.status_code}")
    print(f"    Response: {response.json()}")
    
    # Test 3: Duplicate SKU
    response = requests.post(f"{BASE_URL}/products", json=product_data)
    print(f"  Duplicate SKU: {response.status_code}")
    print(f"    Response: {response.json()}")

def test_low_stock_alerts():
    """Test low stock alerts endpoint"""
    print("\n🔔 Testing GET /companies/1/alerts/low-stock")
    
    response = requests.get(f"{BASE_URL}/companies/1/alerts/low-stock")
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  Total alerts: {data['total_alerts']}")
        print(f"  Company: {data['company_name']}")
        
        for alert in data['alerts'][:3]:  # Show first 3 alerts
            print(f"\n  Alert:")
            print(f"    Product: {alert['product_name']}")
            print(f"    Warehouse: {alert['warehouse_name']}")
            print(f"    Stock: {alert['current_stock']}/{alert['threshold']}")
            print(f"    Days until stockout: {alert['days_until_stockout']}")
            if alert['supplier']:
                print(f"    Supplier: {alert['supplier']['name']}")

def test_get_product():
    """Test getting product details"""
    print("\n🔍 Testing GET /products/1")
    
    response = requests.get(f"{BASE_URL}/products/1")
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        product = response.json()
        print(f"  Product: {product['name']} (SKU: {product['sku']})")
        print(f"  Price: ${product['price']}")
        print(f"  Inventory across warehouses:")
        for inv in product.get('inventory', []):
            print(f"    - Warehouse {inv['warehouse_id']}: {inv['quantity']} units")

def run_all_tests():
    """Run all API tests"""
    print("\n" + "="*50)
    print("🧪 Running API Tests")
    print("="*50)
    
    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/products/1", timeout=2)
    except requests.ConnectionError:
        print("\n❌ ERROR: Server is not running!")
        print("Please run 'python run.py' in another terminal first.")
        return
    
    test_create_product()
    test_get_product()
    test_low_stock_alerts()
    
    print("\n" + "="*50)
    print("✅ Tests completed!")
    print("="*50)

if __name__ == '__main__':
    run_all_tests()