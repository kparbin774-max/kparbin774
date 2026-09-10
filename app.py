from flask import Flask, request, redirect, url_for, render_template_string, session, jsonify
from database import db, init_db, User, Product, KeyStock, StoreSetting
import os
import threading
import telebot
from telebot import types
import qrcode
import io

app = Flask(__name__)
app.secret_key = 'super_secret_master_key_for_shop_99'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)

# ----------------- TELEGRAM BOT SETUP -----------------
BOT_TOKEN = "8973482897:AAFP6GdYlsqIroaJLHIGC_B6ogcXQd2OUvM"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_buy = types.InlineKeyboardButton("🛒 Buy Products", callback_data="buy_products")
    markup.add(btn_buy)
    
    bot.send_message(
        message.chat.id,
        "🔥 **Welcome to Digital Store Bot** 🔥\n\nAutomated instant key delivery!",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "buy_products")
def show_products(call):
    with app.app_context():
        products = Product.query.all()
        if not products:
            bot.send_message(call.message.chat.id, "❌ अभी कोई प्रोडक्ट उपलब्ध नहीं है।")
            return

        markup = types.InlineKeyboardMarkup(row_width=1)
        for p in products:
            stock_count = KeyStock.query.filter_by(product_code=p.product_id, is_used=False).count()
            btn_text = f"🚀 {p.name} - ₹{p.price} ({stock_count} Stock)"
            btn = types.InlineKeyboardButton(btn_text, callback_data=f"select_{p.product_id}")
            markup.add(btn)
        
        bot.send_message(call.message.chat.id, "👇 **खरीदने के लिए प्रोडक्ट चुनें:**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def process_product_selection(call):
    product_id = call.data.split("select_")[1]
    
    with app.app_context():
        setting = StoreSetting.query.first()
        upi_id = setting.current_upi if setting and setting.current_upi else "8292541899@ybl"
    
    upi_payment_url = f"upi://pay?pa={upi_id}&pn=DigitalStore&cu=INR"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_payment_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    bio = io.BytesIO()
    bio.name = 'qr.png'
    img.save(bio)
    bio.seek(0)
    
    markup = types.InlineKeyboardMarkup()
    btn_confirm = types.InlineKeyboardButton("✅ I Have Paid (Get Key)", callback_data=f"confirm_{product_id}")
    markup.add(btn_confirm)
    
    caption = f"📲 **Payment QR Code**\n\n<b>UPI ID:</b> <code>{upi_id}</code>\n\nक्यूआर कोड स्कैन करके पेमेंट करें और 'I Have Paid' पर क्लिक करें।"
    
    bot.send_photo(call.message.chat.id, photo=bio, caption=caption, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_payment(call):
    product_id = call.data.split("confirm_")[1]
    
    with app.app_context():
        key_obj = KeyStock.query.filter_by(product_code=product_id, is_used=False).first()
        if key_obj:
            key_obj.is_used = True
            db.session.commit()
            bot.send_message(
                call.message.chat.id, 
                f"🎉 **Payment Successful!**\n\n🔑 **Your License Key:**\n<code>{key_obj.license_key}</code>",
                parse_mode="HTML"
            )
        else:
            bot.send_message(call.message.chat.id, "❌ स्टॉक खत्म हो गया है!")

def run_bot():
    bot.infinity_polling()

# Start Telegram Bot in a separate Thread
threading.Thread(target=run_bot, daemon=True).start()

# ----------------- HTML TEMPLATES -----------------
LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
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
<head><title>Dashboard</title></head>
<body style="background:#0f172a;color:white;font-family:sans-serif;padding:20px;">
    <h2>🚀 Control Center</h2>
    <p>Active UPI: <b>{{ settings.current_upi if settings else 'Not Set' }}</b></p>
    
    <h3>💳 Update UPI</h3>
    <form method="POST" action="/update_upi">
        <input type="text" name="upi_id" placeholder="UPI ID" required style="padding:8px;">
        <button type="submit">Save UPI</button>
    </form>

    <h3>➕ Add Product</h3>
    <form method="POST" action="/add_product">
        <input type="text" name="product_id" placeholder="Product ID (e.g. ff_hack)" required>
        <input type="text" name="name" placeholder="Name" required>
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

# ----------------- ROUTES -----------------
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
