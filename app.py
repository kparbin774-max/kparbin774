from flask import Flask, request, redirect, url_for, session, render_template_string, jsonify
from database import db, init_db, User, Product, KeyStock, StoreSetting
import os

app = Flask(__name__)
app.secret_key = 'super_secret_master_key_for_shop_999'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)

LOGIN_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot Control Center - Login</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-card { background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); width: 100%; max-width: 400px; text-align: center; }
        h2 { margin-bottom: 24px; color: #38bdf8; }
        input { width: 100%; padding: 12px; margin-bottom: 20px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: white; font-size: 16px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #38bdf8; border: none; border-radius: 8px; color: #0f172a; font-weight: bold; font-size: 16px; cursor: pointer; transition: 0.3s; }
        button:hover { background: #0ea5e9; }
        .error { color: #f43f5e; margin-bottom: 15px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🔐 Admin Control</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="password" name="password" placeholder="Enter Admin Password" required>
            <button type="submit">Unlock Dashboard</button>
        </form>
    </div>
</body>
</html>
'''

DASHBOARD_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shop Control Center - Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 1px solid #334155; padding-bottom: 15px; }
        h1 { color: #38bdf8; margin: 0; font-size: 24px; }
        .logout { background: #f43f5e; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: #1e293b; padding: 20px; border-radius: 10px; border-left: 4px solid #38bdf8; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .stat-card h3 { margin: 0 0 10px 0; color: #94a3b8; font-size: 14px; }
        .stat-card p { margin: 0; font-size: 24px; font-weight: bold; color: #f8fafc; }
        .section { background: #1e293b; padding: 25px; border-radius: 10px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h2 { margin-top: 0; color: #38bdf8; font-size: 18px; border-bottom: 1px solid #334155; padding-bottom: 10px; }
        form input, form select, form textarea { width: 100%; padding: 12px; margin-bottom: 15px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: white; box-sizing: border-box; font-size: 15px; }
        form button { background: #10b981; color: white; border: none; padding: 12px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px; transition: 0.3s; }
        form button:hover { background: #059669; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚡ Shop Control Center</h1>
            <a href="/logout" class="logout">Logout</a>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Members</h3>
                <p>{{ total_members }}</p>
            </div>
            <div class="stat-card">
                <h3>Total Products</h3>
                <p>{{ total_products }}</p>
            </div>
            <div class="stat-card">
                <h3>Active UPI</h3>
                <p style="font-size: 18px; color: #10b981;">{{ settings.current_upi if settings and settings.current_upi else 'Not Set' }}</p>
            </div>
        </div>

        <div class="section">
            <h2>🛍️ Add New Product</h2>
            <form method="POST" action="/add_product">
                <input type="text" name="product_id" placeholder="Product ID (e.g., ff_1_month)" required>
                <input type="text" name="name" placeholder="Product Name (e.g., Free Fire Evo Skin)" required>
                <input type="number" step="0.01" name="price" placeholder="Price in INR (e.g., 199.0)" required>
                <input type="text" name="duration" placeholder="Duration (e.g., 30 Days)" required>
                <button type="submit">Add Product</button>
            </form>
        </div>

        <div class="section">
            <h2>🔑 Add License Keys</h2>
            <form method="POST" action="/add_keys">
                <input type="text" name="product_code" placeholder="Product ID to link keys" required>
                <textarea name="keys" rows="4" placeholder="Paste keys here (one key per line)" required></textarea>
                <button type="submit">Upload Keys</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'admin123':
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
        error = "Incorrect Password! Try again."
    return render_template_string(LOGIN_PAGE, error=error)

@app.route('/')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    total_members = User.query.count()
    total_products = Product.query.count()
    settings = StoreSetting.query.first()
    
    return render_template_string(DASHBOARD_PAGE, total_members=total_members, total_products=total_products, settings=settings)

@app.route('/add_product', methods=['POST'])
def add_product():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    pid = request.form.get('product_id')
    name = request.form.get('name')
    price = float(request.form.get('price'))
    duration = request.form.get('duration')
    
    if not Product.query.filter_by(product_id=pid).first():
        new_prod = Product(product_id=pid, name=name, price=price, duration=duration)
        db.session.add(new_prod)
        db.session.commit()
        
    return redirect(url_for('dashboard'))

@app.route('/add_keys', methods=['POST'])
def add_keys():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
        
    pcode = request.form.get('product_code')
    raw_keys = request.form.get('keys')
    
    if raw_keys:
        key_list = raw_keys.split('\n')
        for k in key_list:
            clean_k = k.strip()
            if clean_k and not KeyStock.query.filter_by(license_key=clean_k).first():
                new_key = KeyStock(product_code=pcode, license_key=clean_k, is_used=False)
                db.session.add(new_key)
        db.session.commit()
        
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
