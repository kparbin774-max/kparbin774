import telebot

TOKEN = '8798842120:AAHk6Oiw7r_bXU1IVfv0ynJuHoquX-wtPyI'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "नमस्ते! आपका अपना बोट लाइव हो गया है।")

bot.infinity_polling()
