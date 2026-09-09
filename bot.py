import telebot

TOKEN = '8973482897:AAFP6GdYlsqIroaJLHIGC_B6ogcXQd2OUvM'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "नमस्ते! आपका नया बोट (Lebetastor_bot) सफलतापूर्वक लाइव हो गया है।")

bot.infinity_polling()
