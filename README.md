# StockFlow - B2B Inventory Management System

A REST API built with Python/Flask and MySQL for managing inventory across multiple warehouses.

## Tech Stack
- Python 3.11 | Flask | MySQL | SQLAlchemy | Flask-Migrate

## Setup
```bash
pip install -r requirements.txt
flask db upgrade
python seed_data.py
python run.py
```

## API Endpoints
| Method | Endpoint | Description |
|---|---|---|
| POST | /api/products | Create product |
| GET | /api/products/<id> | Get product details |
| PUT | /api/products/<id>/inventory | Update inventory |
| GET | /api/companies/<id>/alerts/low-stock | Low stock alerts |

## Submission
- Part 1: Code Review & Debugging
- Part 2: Database Design  
- Part 3: API Implementation
- Part 4: Live API Testing (Postman)

**Author:** Dinesh | April 2026
