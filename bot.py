import os
import sqlite3
from threading import Thread
from flask import Flask, redirect, render_template_string, request, url_for
import telebot

TOKEN = "8973482897:AAFP6GdYlsqIroaJLHIGC_B6ogcXQd2OUvM"
ADMIN_ID = 6680567083

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- Database Setup ---
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

  # Default UPI ID अगर सेट न हो
  cursor.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('upi_id',"
      " 'yourname@upi')"
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


# --- HTML Template for Web Admin Panel ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot Admin Control Center</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: auto; background: #1e293b; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h1, h2 { color: #38bdf8; text-align: center; }
        .card { background: #334155; padding: 15px; margin-bottom: 15px; border-radius: 8px; }
        input, select { width: 100%; padding: 10px; margin: 8px 0; background: #0f172a; border: 1px solid #475569; color: white; border-radius: 6px; box-sizing: border-box; }
        button { background: #0284c7; color: white; border: none; padding: 10px 15px; width: 100%; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 5px; }
        button:hover { background: #0369a1; }
        .danger { background: #dc2626; }
        .danger:hover { background: #b91c1c; }
        ul { padding-left: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚙️ Bot Admin Panel</h1>
        
        <!-- UPI Settings -->
        <div class="card">
            <h2>💳 UPI Payment Settings</h2>
            <form method="POST" action="/update_upi">
                <label>Current UPI ID:</label>
                <input type="text" name="upi_id" value="{{ upi_id }}" required>
                <button type="submit">Update UPI ID</button>
            </form>
        </div>

        <!-- Add Product -->
        <div class="card">
            <h2>📦 Add New Product</h2>
            <form method="POST" action="/add_product">
                <input type="text" name="p_id" placeholder="Product ID (e.g., esp_hack)" required>
                <input type="text" name="p_name" placeholder="Product Name (e.g., ESP HACK PRO)" required>
                <input type="number" name="p_price" placeholder="Price in INR (e.g., 199)" required>
                <input type="text" name="p_duration" placeholder="Duration (e.g., 1 Month)" required>
                <button type="submit">Add Product</button>
            </form>
        </div>

        <!-- Add Keys to Stock -->
        <div class="card">
            <h2>🔑 Add Key Stock</h2>
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

        <!-- Current Products & Stock Status -->
        <div class="card">
            <h2>📊 Live Products & Stock</h2>
            <ul>
                {% for p in products %}
                <li><b>{{ p[1] }}</b> (₹{{ p[2] }}) - Stock: {{ stock_counts[p[0]] }} Keys</li>
                {% endfor %}
            </ul>
        </div>
    </div>
</body>
</html>
"""


# --- Flask Web Routes ---
@app.route("/")
def admin_home():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("SELECT value FROM settings WHERE key='upi_id'")
  upi_row = cursor.fetchone()
  upi_id = upi_row[0] if upi_row else "yourname@upi"

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
      HTML_TEMPLATE,
      upi_id=upi_id,
      products=products,
      stock_counts=stock_counts,
  )


@app.route("/update_upi", methods=["POST"])
def update_upi():
  new_upi = request.form.get("upi_id")
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      "UPDATE settings SET value = ? WHERE key = 'upi_id'", (new_upi,)
  )
  conn.commit()
  conn.close()
  return redirect(url_for("admin_home"))


@app.route("/add_product", methods=["POST"])
def add_product():
  p_id = request.form.get("p_id").strip().lower()
  p_name = request.form.get("p_name")
  p_price = int(request.form.get("p_price"))
  p_duration = request.form.get("p_duration")

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      "INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?)",
      (p_id, p_name, p_price, p_duration),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("admin_home"))


@app.route("/add_key", methods=["POST"])
def add_key():
  p_id = request.form.get("product_id")
  key_text = request.form.get("license_key")

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("INSERT INTO keys_stock VALUES (?, ?)", (p_id, key_text))
  conn.commit()
  conn.close()
  return redirect(url_for("admin_home"))


# --- Telegram Bot Logic ---
@bot.message_handler(commands=["start"])
def send_welcome(message):
  markup = telebot.types.InlineKeyboardMarkup()
  markup.row_width = 2
  markup.add(
      telebot.types.InlineKeyboardButton(
          "📦 Buy Products", callback_data="show_products"
      ),
      telebot.types.InlineKeyboardButton(
          "⚙️ Admin Panel Link", callback_data="admin_info"
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

    # डेटाबेस से करंट UPI ID फेच करें
    cursor.execute("SELECT value FROM settings WHERE key='upi_id'")
    upi_row = cursor.fetchone()
    current_upi = upi_row[0] if upi_row else "yourname@upi"

    pay_markup = telebot.types.InlineKeyboardMarkup()
    pay_markup.add(
        telebot.types.InlineKeyboardButton(
            "✅ Payment Ho Gaya (Get Key)", callback_data=f"verify_{product_key}"
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
            f" `₹{p_price}`\nDuration: `{p_dur}`\n\nकृपया नीचे दी गई UPI ID पर"
            f" पेमेंट करें:\n👉 `{current_upi}`\n\nपेमेंट पूरा करने के बाद नीचे"
            " दिए गए बटन पर क्लिक करें:"
        ),
        reply_markup=pay_markup,
        parse_mode="Markdown",
    )

  elif call.data.startswith("verify_"):
    product_key = call.data.replace("verify_", "")
    cursor.execute(
        "SELECT license_key FROM keys_stock WHERE product_id = ?", (product_key,)
    )
    row = cursor.fetchone()

    if row:
      delivered_key = row[0]
      cursor.execute(
          "DELETE FROM keys_stock WHERE product_id = ? AND license_key = ?",
          (product_key, delivered_key),
      )
      conn.commit()

      bot.edit_message_text(
          chat_id=call.message.chat.id,
          message_id=call.message.message_id,
          text=(
              "🎉 **Payment Verified & Key"
              f" Delivered!**\n\nYour License Key:\n`{delivered_key}`\n\nइसे"
              " कॉपी करके गेम में इस्तेमाल करें। धन्यवाद!"
          ),
          parse_mode="Markdown",
      )
    else:
      bot.answer_callback_query(
          call.id,
          "❌ Stock empty ho gaya hai! Admin se sampark karein.",
          show_alert=True,
      )

  elif call.data == "admin_info":
    bot.answer_callback_query(
        call.id,
        "वेब एडमिन पैनल खोलने के लिए अपने Render ऐप का लिंक ब्राउज़र में"
        " खोलें।",
        show_alert=True,
    )

  elif call.data == "back_home":
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        telebot.types.InlineKeyboardButton(
            "📦 Buy Products", callback_data="show_products"
        ),
        telebot.types.InlineKeyboardButton(
            "⚙️ Admin Panel Link", callback_data="admin_info"
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


# --- Run Flask and Telegram Bot Simultaneously ---
def run_flask():
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
  # Flask को बैकग्राउंड में चलाने के लिए Thread का इस्तेमाल
  t = Thread(target=run_flask)
  t.start()

  # Telegram Bot Polling
  bot.infinity_polling()
