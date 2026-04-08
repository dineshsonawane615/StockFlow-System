"""
StockFlow - B2B Inventory Management System
Main application factory
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://root:dinesh@localhost:3306/stockflow_db'  # ← change this
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    # Override with custom config if provided
    if config:
        app.config.update(config)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import and register blueprints (routes)
    from app.routes import products, alerts
    
    app.register_blueprint(products.bp)
    app.register_blueprint(alerts.bp)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app