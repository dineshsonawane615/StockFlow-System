"""
StockFlow Application Entry Point
Run this file to start the server
"""

from app import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("📦 StockFlow Inventory Management System")
    print("="*50)
    print("\n✅ Server is starting...")
    print("📍 Running at: http://localhost:5000")
    print("\n📋 Available Endpoints:")
    print("   POST   /api/products - Create new product")
    print("   GET    /api/products/<id> - Get product details")
    print("   PUT    /api/products/<id>/inventory - Update inventory")
    print("   GET    /api/companies/<id>/alerts/low-stock - Get low stock alerts")
    print("\n⚠️  Press CTRL+C to stop the server")
    print("="*50 + "\n")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)