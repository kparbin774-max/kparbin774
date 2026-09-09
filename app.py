from flask import Flask, request, redirect, url_for, session, jsonify
from database import db, init_db, User, Product, StoreSetting
import os

app = Flask(__name__)
app.secret_key = 'super_secret_master_key_here'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'admin123':  # यहाँ अपना ओनर पासवर्ड बदल सकते हैं
            session['admin_logged_in'] = True
            return redirect(url_for('dashboard'))
        return "Wrong Password! <a href='/login'>Try Again</a>"
    return '''
        <h2>Bot Control Center - Login</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Enter Admin Password" required>
            <button type="submit">Unlock</button>
        </form>
    '''

@app.route('/')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    total_members = User.query.count()
    total_catalog = Product.query.count()
    settings = StoreSetting.query.first()
    
    return jsonify({
        "status": "Success",
        "message": "Welcome to Bot Control Center Dashboard",
        "total_members": total_members,
        "catalog_items": total_catalog,
        "shop_name": settings.shop_name if settings else "Default Shop"
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
