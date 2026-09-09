from flask_sqlalchemy import SQLAlchemy
from flask import Flask

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

# 1. User & Members Table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='User') # Admin / User / Reseller
    wallet_balance = db.Column(db.Float, default=0.0)
    deposited_today = db.Column(db.Float, default=0.0)

# 2. Products Table
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Active') # Active / Maintenance

# 3. Key Stock Table
class KeyStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(50), nullable=False)
    license_key = db.Column(db.String(255), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

# 4. Store Settings Table
class StoreSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), default='My Shop')
    tagline = db.Column(db.String(200), default='')
    support_username = db.Column(db.String(100), default='')
    current_upi = db.Column(db.String(100), default='')
    min_deposit = db.Column(db.Float, default=10.0)
    max_deposit = db.Column(db.Float, default=50000.0)
