from flask import Flask, request, redirect, url_for, render_template_string, session, jsonify
from database import db, init_db, User, Product, KeyStock, StoreSetting
import os

app = Flask(__name__)
app.secret_key = 'super_secret_master_key_for_shop_99'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)

LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head><title>Admin Login</title></head>
<body style="background:#0f172a;color:white;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;">
    <form method="POST" style="background:#1e293b;padding:30px;border-radius:10px;text-align:center;">
        <h2>Admin Login</h2>
        <input type="password" name="password" placeholder="Password" required style="padding:10px;margin-bottom:10px;width:100%;"><br>
        <button type="submit" style="padding:10px;width:100%;background:#38bdf8;border:none;border-radius:5px;font-weight:bold;">Login</button>
    </form>
</body>
</html>
'''

DASHBOARD_PAGE = '''
<!DOCTYPE html>
<html>
<head><title>Control Center</title></head>
<body style="background:#0f172a;color:white;font-family:sans-serif;padding:20px;">
    <h2>🚀 Shop Control Center</h2>
    <p>Active UPI: <b>{{ settings.current_upi if settings else 'Not Set' }}</b></p>
    
    <h3>💳 Payment Settings</h3>
    <form method="POST" action="/update_upi">
        <input type="text" name="upi_id" placeholder="UPI ID" required style="padding:8px;">
        <button type="submit">Save UPI</button>
    </form>

    <h3>➕ Add Product</h3>
    <form method="POST" action="/add_product">
        <input type="text" name="product_id" placeholder="Product ID (e.g. ff_hack)" required>
        <input type="text" name="name" placeholder="Product Name" required>
        <input type="number" step="0.01" name="price" placeholder="Price" required>
        <input type="text" name="duration" placeholder="Duration" required>
        <button type="submit">Add Product</button>
    </form>

    <h3>🔑 Add Keys</h3>
    <form method="POST" action="/add_keys">
        <input type="text" name="product_code" placeholder="Product ID" required><br><br>
        <textarea name="keys" rows="4" placeholder="Keys (one per line)" required></textarea><br>
        <button type="submit">Upload Keys</button>
    </form>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == 'admin123':
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_PAGE)

@app.route('/')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    settings = StoreSetting.query.first()
    return render_template_string(DASHBOARD_PAGE, settings=settings)

@app.route('/update_upi', methods=['POST'])
def update_upi():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    upi_id = request.form.get('upi_id')
    settings = StoreSetting.query.first()
    if not settings:
        settings = StoreSetting(current_upi=upi_id)
        db.session.add(settings)
    else:
        settings.current_upi = upi_id
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_product', methods=['POST'])
def add_product():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    pid = request.form.get('product_id')
    name = request.form.get('name')
    price = float(request.form.get('price'))
    duration = request.form.get('duration')
    if not Product.query.filter_by(product_id=pid).first():
        db.session.add(Product(product_id=pid, name=name, price=price, duration=duration))
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_keys', methods=['POST'])
def add_keys():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    pcode = request.form.get('product_code')
    raw_keys = request.form.get('keys')
    if raw_keys:
        for k in raw_keys.split('\n'):
            clean_k = k.strip()
            if clean_k:
                db.session.add(KeyStock(product_code=pcode, license_key=clean_k, is_used=False))
        db.session.commit()
    return redirect(url_for('dashboard'))

# ------------ API ENDPOINTS FOR TELEGRAM BOT ------------
@app.route('/api/get_products', methods=['GET'])
def api_get_products():
    products = Product.query.all()
    setting = StoreSetting.query.first()
    upi_id = setting.current_upi if setting else "8292541899@ybl"
    
    data = []
    for p in products:
        stock_count = KeyStock.query.filter_by(product_code=p.product_id, is_used=False).count()
        data.append({
            'product_id': p.product_id,
            'name': p.name,
            'price': p.price,
            'duration': p.duration,
            'stock': stock_count
        })
    return jsonify({'status': 'success', 'upi_id': upi_id, 'products': data})

@app.route('/api/buy_key', methods=['POST'])
def api_buy_key():
    req = request.get_json() or {}
    product_id = req.get('product_id')
    
    key_obj = KeyStock.query.filter_by(product_code=product_id, is_used=False).first()
    if key_obj:
        key_obj.is_used = True
        db.session.commit()
        return jsonify({'status': 'success', 'key': key_obj.license_key})
    return jsonify({'status': 'error', 'message': 'Out of stock'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
