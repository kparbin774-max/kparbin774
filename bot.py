import telebot
from telebot import types
import requests
import qrcode
import io

BOT_TOKEN = "8973482897:AAFP6GdYlsqIroaJLHIGC_B6ogcXQd2OUvM"
WEB_URL = "https://kparbin774python-bot-py.onrender.com"

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
    try:
        response = requests.get(f"{WEB_URL}/api/get_products")
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            
            if not products:
                bot.send_message(call.message.chat.id, "❌ वेबसाइट पर कोई प्रोडक्ट नहीं मिला। कृपया Admin Dashboard में Product जोड़ें।")
                return

            markup = types.InlineKeyboardMarkup(row_width=1)
            for p in products:
                # स्टॉक 0 होने पर भी प्रोडक्ट दिखेगा
                stock_text = f"{p['stock']} Stock" if p['stock'] > 0 else "Out of Stock"
                btn_text = f"🚀 {p['name']} - ₹{p['price']} ({stock_text})"
                btn = types.InlineKeyboardButton(btn_text, callback_data=f"select_{p['product_id']}")
                markup.add(btn)
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="👇 **खरीदने के लिए प्रोडक्ट चुनें:**",
                reply_markup=markup
            )
        else:
            bot.send_message(call.message.chat.id, "❌ सर्वर से कनेक्शन फेल हो गया।")
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ एरर: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def process_product_selection(call):
    product_id = call.data.split("select_")[1]
    
    # UPI ID
    upi_id = "8292541899@ybl"
    
    # QR Code बनाना
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
    
    caption = f"📲 **Payment QR Code**\n\n<b>UPI ID:</b> <code>{upi_id}</code>\n\nQR Code को स्कैन करके पेमेंट करें और नीचे 'I Have Paid' पर टैप करें।"
    
    bot.send_photo(call.message.chat.id, photo=bio, caption=caption, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirm_payment(call):
    product_id = call.data.split("confirm_")[1]
    
    try:
        res = requests.post(f"{WEB_URL}/api/buy_key", json={"product_id": product_id})
        if res.status_code == 200:
            result = res.json()
            if result.get('status') == 'success':
                key = result.get('key')
                bot.send_message(
                    call.message.chat.id, 
                    f"🎉 **Payment Successful!**\n\n🔑 **Your License Key:**\n<code>{key}</code>",
                    parse_mode="HTML"
                )
            else:
                bot.send_message(call.message.chat.id, "❌ इस प्रोडक्ट का स्टॉक खत्म है (Out of Stock)। वेबसाइट पर Keys जोड़ें।")
        else:
            bot.send_message(call.message.chat.id, "❌ पेमेंट प्रोसेसिंग में समस्या आई।")
    except Exception as e:
        bot.send_message(call.message.chat.id, "❌ सर्वर एरर।")

if __name__ == "__main__":
    bot.infinity_polling()
