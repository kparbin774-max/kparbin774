import os
import sqlite3
from threading import Thread
from flask import Flask, redirect, render_template_string, request, url_for
import telebot

# --- Database & Config Setup ---
def init_db():
  conn = sqlite3.connect("store.db", check_same_thread=False)
  cursor = conn.cursor()
  cursor.execute(
      """CREATE TABLE IF NOT EXISTS settings 
                    (key TEXT PRIMARY KEY, value TEXT)"""
  )
  cursor.execute(
      """CREATE TABLE IF NOT EXISTS products 
                    (id TEXT PRIMARY KEY, name TEXT, price INTEGER, duration TEXT)"""
  )
  cursor.execute(
      """CREATE TABLE IF NOT EXISTS keys_stock 
                    (product_id TEXT, license_key TEXT)"""
  )
  cursor.execute(
      """CREATE TABLE IF NOT EXISTS pending_orders 
                    (order_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT, product_id TEXT, product_name TEXT, price INTEGER)"""
  )

  # Default Settings
  cursor.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('upi_id',"
      " '8292541899@ybl')"
  )
  cursor.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('bot_token',"
      " '8973482897:AAFP6GdYlsqIroaJLHIGC_B6ogcXQd2OUvM')"
  )
  cursor.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('admin_id',"
      " '6680567083')"
  )

  # Default Products
  cursor.execute("SELECT COUNT(*) FROM products")
  if cursor.fetchone()[0] == 0:
    cursor.execute(
        "INSERT INTO products VALUES ('aim_hack', '🚀 AIM HACK NONROOT', 100,"
        " '1 Day')"
    )
    cursor.execute(
        "INSERT INTO products VALUES ('haxx_cher', '🔥 HAXX CHER PRO', 150,"
        " '1 Day')"
    )
    cursor.execute(
        "INSERT INTO keys_stock VALUES ('aim_hack', 'AIM-DEMO-KEY-111')"
    )
    cursor.execute(
        "INSERT INTO keys_stock VALUES ('haxx_cher', 'HAXX-DEMO-KEY-999')"
    )

  conn.commit()
  conn.close()


init_db()


def get_db_connection():
  return sqlite3.connect("store.db", check_same_thread=False)


def get_settings():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT key, value FROM settings")
  rows = cursor.fetchall()
  conn.close()
  return {row[0]: row[1] for row in rows}


config = get_settings()
bot = telebot.TeleBot(config.get("bot_token", ""))
app = Flask(__name__)

# --- Exact Video Look & Feel HTML Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot Admin Panel</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0b1120;
            color: #e2e8f0;
            margin: 0;
            padding: 10px;
        }
        .container {
            max-width: 480px;
            margin: 0 auto;
            background: #111827;
            padding: 20px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8);
            border: 1px solid #1f2937;
        }
        h1 {
            text-align: center;
            font-size: 24px;
            color: #ffffff;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .section-card {
            background: #1f2937;
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 16px;
            border: 1px solid #374151;
        }
        .section-title {
            font-size: 16px;
            font-weight: 600;
            color: #f3f4f6;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        label {
            display: block;
            font-size: 13px;
            color: #9ca3af;
            margin-bottom: 6px;
        }
        input, select {
            width: 100%;
            padding: 12px;
            background: #0b1120;
            border: 1px solid #374151;
            color: #ffffff;
            border-radius: 10px;
            font-size: 14px;
            margin-bottom: 12px;
            box-sizing: border-box;
        }
        input:focus, select:focus {
            border-color: #3b82f6;
            outline: none;
        }
        button {
            background: #2563eb;
            color: white;
            border: none;
            width: 100%;
            padding: 12px;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover {
            background: #1d4ed8;
        }
        .stock-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .stock-item {
            background: #111827;
            padding: 10px 14px;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 14px;
            border: 1px solid #374151;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .badge {
            background: #374151;
            color: #60a5fa;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ Bot Admin Panel</h1>
        
        <!-- UPI & API Settings -->
        <div class="section-card">
            <div class="section-title">💳 UPI Payment & API Settings</div>
            <form method="POST" action="/update_settings">
                <label>Bot Telegram Token:</label>
                <input type="text" name="bot_token" value="{{ settings.bot_token }}" required>
                
                <label>Admin Telegram ID:</label>
                <input type="text" name="admin_id" value="{{ settings.admin_id }}" required>

                <label>Current UPI ID:</label>
                <input type="text" name="upi_id" value="{{ settings.upi_id }}" required>
                
                <button type="submit">Update Settings</button>
            </form>
        </div>

        <!-- Add New Product -->
        <div class="section-card">
            <div class="section-title">📦 Add New Product</div>
            <form method="POST" action="/add_product">
                <input type="text" name="p_id" placeholder="Product ID (e.g., aim_hack)" required>
                <input type="text" name="p_name" placeholder="Product Name (e.g., ESP HACK PRO)" required>
                <input type="number" name="p_price" placeholder="Price in INR (e.g., 199)" required>
                <input type="text" name="p_duration" placeholder="Duration (e.g., 1 Month)" required>
                <button type="submit">Add Product</button>
            </form>
        </div>

        <!-- Add Key Stock -->
        <div class="section-card">
            <div class="section-title">🔑 Add Key Stock</div>
            <form method="POST" action="/add_key">
                <select name="product_id">
                    {% for p in products %}
                    <option value="{{ p[0] }}">{{ p[1] }}</option>
                    {% endfor %}
                </select>
                <input type="text" name="license_key" placeholder="Enter Secret License Key" required>
                <button type="submit">Add Key to Stock</button>
            </form>
        </div>

        <!-- Live Products & Stock -->
        <div class="section-card">
            <div class="section-title">📊 Live Products & Stock</div>
            <ul class="stock-list">
                {% for p in products %}
                <li class="stock-item">
                    <span><b>{{ p[1] }}</b> (₹{{ p[2] }})</span>
                    <span class="badge">Stock: {{ stock_counts[p[0]] }} Keys</span>
                </li>
                {% endfor %}
            </ul>
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def admin_home():
  conn = get_db_connection()
  cursor = conn.cursor()
  settings = get_settings()
  cursor.execute("SELECT * FROM products")
  products = cursor.fetchall()
  stock_counts = {}
  for p in products:
    cursor.execute(
        "SELECT COUNT(*) FROM keys_stock WHERE product_id = ?", (p[0],)
    )
    stock_counts[p[0]] = cursor.fetchone()[0]
  conn.close()
  return render_template_string(
      HTML_TEMPLATE, settings=settings, products=products, stock_counts=stock_counts
  )


@app.route("/update_settings", methods=["POST"])
def update_settings():
  conn = get_db_connection()
  cursor = conn.cursor()
  new_token = request.form.get("bot_token")
  cursor.execute("UPDATE settings SET value = ? WHERE key = 'bot_token'", (new_token,))
  cursor.execute(
      "UPDATE settings SET value = ? WHERE key = 'admin_id'",
      (request.form.get("admin_id"),),
  )
  cursor.execute(
      "UPDATE settings SET value = ? WHERE key = 'upi_id'",
      (request.form.get("upi_id"),),
  )
  conn.commit()
  conn.close()
  global bot
  bot.token = new_token
  return redirect(url_for("admin_home"))


@app.route("/add_product", methods=["POST"])
def add_product():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      "INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?)",
      (
          request.form.get("p_id").strip().lower(),
          request.form.get("p_name"),
          int(request.form.get("p_price")),
          request.form.get("p_duration"),
      ),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("admin_home"))


@app.route("/add_key", methods=["POST"])
def add_key():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO keys_stock VALUES (?, ?)",
      (request.form.get("product_id"), request.form.get("license_key")),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("admin_home"))


# --- Telegram Bot Logic with Admin Verification ---
@bot.message_handler(commands=["start"])
def send_welcome(message):
  markup = telebot.types.InlineKeyboardMarkup(row_width=2)
  markup.add(
      telebot.types.InlineKeyboardButton(
          "📦 Buy Products", callback_data="show_products"
      ),
      telebot.types.InlineKeyboardButton(
          "⚙️ Admin Panel", callback_data="admin_info"
      ),
  )
  bot.send_message(
      message.chat.id,
      "🔥 **Digital Store Bot** 🔥\n\nTrusted products, instant automated key"
      " delivery.\nWelcome!",
      reply_markup=markup,
      parse_mode="Markdown",
  )


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
  conn = get_db_connection()
  cursor = conn.cursor()
  settings = get_settings()
  admin_id = int(settings.get("admin_id", "6680567083"))

  if call.data == "show_products":
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    products_markup = telebot.types.InlineKeyboardMarkup()
    for prod in products:
      p_id, p_name, p_price, p_dur = prod
      cursor.execute(
          "SELECT COUNT(*) FROM keys_stock WHERE product_id = ?", (p_id,)
      )
      stock_count = cursor.fetchone()[0]
      btn_text = f"{p_name} - ₹{p_price} ({stock_count} Available)"
      products_markup.add(
          telebot.types.InlineKeyboardButton(
              btn_text, callback_data=f"buy_{p_id}"
          )
      )
    products_markup.add(
        telebot.types.InlineKeyboardButton(
            "🔙 Main Menu", callback_data="back_home"
        )
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="👇 **Available Products & Stock:** खरीदने के लिए प्रोडक्ट चुनें:",
        reply_markup=products_markup,
        parse_mode="Markdown",
    )

  elif call.data.startswith("buy_"):
    product_key = call.data.replace("buy_", "")
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_key,))
    prod = cursor.fetchone()
    if not prod:
      bot.answer_callback_query(call.id, "Product nahi mila!", show_alert=True)
      conn.close()
      return

    p_id, p_name, p_price, p_dur = prod
    cursor.execute(
        "SELECT COUNT(*) FROM keys_stock WHERE product_id = ?", (product_key,)
    )
    stock_count = cursor.fetchone()[0]

    if stock_count == 0:
      bot.answer_callback_query(
          call.id,
          "❌ Maaf kijiye, yeh product abhi Out of Stock hai!",
          show_alert=True,
      )
      conn.close()
      return

    current_upi = settings.get("upi_id", "8292541899@ybl")
    pay_link = (
        f"upi://pay?pa={current_upi}&pn=DigitalStore&am={p_price}&cu=INR"
    )

    pay_markup = telebot.types.InlineKeyboardMarkup()
    pay_markup.add(
        telebot.types.InlineKeyboardButton(
            "🔗 Pay via UPI App", url=pay_link
        )
    )
    pay_markup.add(
        telebot.types.InlineKeyboardButton(
            "✅ Payment Ho Gaya (Verify)",
            callback_data=f"verify_pay_{product_key}",
        )
    )
    pay_markup.add(
        telebot.types.InlineKeyboardButton(
            "🔙 Back", callback_data="show_products"
        )
    )

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(
            f"🛒 **Payment Details**\n\nProduct: `{p_name}`\nPrice:"
            f" `₹{p_price}`\nDuration: `{p_dur}`\n\nUPI ID: `{current_upi}`\n\nकृपया"
            " ऊपर दिए गए लिंक से पेमेंट करें या UPI ID पर पैसे भेजें। पेमेंट"
            " करने के बाद **'Payment Ho Gaya'** बटन पर क्लिक करें।"
        ),
        reply_markup=pay_markup,
        parse_mode="Markdown",
    )

  elif call.data.startswith("verify_pay_"):
    product_key = call.data.replace("verify_pay_", "")
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_key,))
    prod = cursor.fetchone()

    if prod:
      p_id, p_name, p_price, p_dur = prod
      user_id = call.from_user.id
      username = (
          f"@{call.from_user.username}"
          if call.from_user.username
          else call.from_user.first_name
      )

      cursor.execute(
          "INSERT INTO pending_orders (user_id, username, product_id,"
          " product_name, price) VALUES (?, ?, ?, ?, ?)",
          (user_id, username, p_id, p_name, p_price),
      )
      order_id = cursor.lastrowid
      conn.commit()

      admin_markup = telebot.types.InlineKeyboardMarkup(row_width=2)
      admin_markup.add(
          telebot.types.InlineKeyboardButton(
              "✅ Approve & Send Key", callback_data=f"approve_{order_id}"
          ),
          telebot.types.InlineKeyboardButton(
              "❌ Reject", callback_data=f"reject_{order_id}"
          ),
      )

      try:
        bot.send_message(
            admin_id,
            f"🔔 **New Payment Request!**\n\nUser: {username} (`{user_id}`)\nProduct:"
            f" `{p_name}`\nAmount: `₹{p_price}`\n\nकृपया चेक करें:",
            reply_markup=admin_markup,
            parse_mode="Markdown",
        )
      except Exception as e:
        print(f"Admin error: {e}")

      bot.edit_message_text(
          chat_id=call.message.chat.id,
          message_id=call.message.message_id,
          text=(
              "⏳ **Payment Verification Pending**\n\nआपका पेमेंट अनुरोध एडमिन के"
              " पास भेज दिया गया है। चेक होने के बाद की (Key) मिल जाएगी।"
          ),
          parse_mode="Markdown",
      )

  elif call.data.startswith("approve_"):
    if call.from_user.id != admin_id:
      bot.answer_callback_query(
          call.id, "Aap Admin nahi hain!", show_alert=True
      )
      conn.close()
      return

    order_id = int(call.data.replace("approve_", ""))
    cursor.execute(
        "SELECT user_id, product_id, product_name FROM pending_orders WHERE"
        " order_id = ?",
        (order_id,),
    )
    order = cursor.fetchone()

    if order:
      target_user_id, p_id, p_name = order
      cursor.execute(
          "SELECT license_key FROM keys_stock WHERE product_id = ?", (p_id,)
      )
      row = cursor.fetchone()

      if row:
        delivered_key = row[0]
        cursor.execute(
            "DELETE FROM keys_stock WHERE product_id = ? AND license_key = ?",
            (p_id, delivered_key),
        )
        cursor.execute(
            "DELETE FROM pending_orders WHERE order_id = ?", (order_id,)
        )
        conn.commit()

        try:
          bot.send_message(
              target_user_id,
              f"🎉 **Payment Verified & Key"
              f" Delivered!**\n\nProduct: `{p_name}`\nYour License"
              f" Key:\n`{delivered_key}`\n\nधन्यवाद!",
              parse_mode="Markdown",
          )
        except Exception as e:
          print(f"User error: {e}")

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=(
                f"✅ **Approved!** Key `{delivered_key}` user ko bhej di gayi"
                " hai."
            ),
        )
      else:
        bot.answer_callback_query(
            call.id,
            "❌ Stock empty hai! Pehle website se key add karein.",
            show_alert=True,
        )

  elif call.data.startswith("reject_"):
    if call.from_user.id != admin_id:
      bot.answer_callback_query(
          call.id, "Aap Admin nahi hain!", show_alert=True
      )
      conn.close()
      return

    order_id = int(call.data.replace("reject_", ""))
    cursor.execute(
        "SELECT user_id FROM pending_orders WHERE order_id = ?", (order_id,)
    )
    order = cursor.fetchone()
    if order:
      target_user_id = order[0]
      cursor.execute(
          "DELETE FROM pending_orders WHERE order_id = ?", (order_id,)
      )
      conn.commit()
      try:
        bot.send_message(
            target_user_id,
            "❌ **Payment Rejected!**\nआपका पेमेंट वेरीफाई नहीं हो पाया।",
            parse_mode="Markdown",
        )
      except:
        pass
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="❌ Order Rejected.",
    )

  elif call.data == "admin_info":
    bot.answer_callback_query(
        call.id, "Web Admin Panel link: apne Render dashboard par dekhein.", show_alert=True
    )

  elif call.data == "back_home":
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton(
            "📦 Buy Products", callback_data="show_products"
        ),
        telebot.types.InlineKeyboardButton(
            "⚙️ Admin Panel", callback_data="admin_info"
        ),
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=(
            "🔥 **Digital Store Bot** 🔥\n\nTrusted products, instant automated"
            " key delivery.\nWelcome!"
        ),
        reply_markup=markup,
        parse_mode="Markdown",
    )

  conn.close()


def run_flask():
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
  t = Thread(target=run_flask)
  t.start()
  bot.infinity_polling()
