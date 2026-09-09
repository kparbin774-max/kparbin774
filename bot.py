import telebot

TOKEN = '8947694806:AAHOreaOcZTJmhnBu8Wu6iCEMYesNLn_agE'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "नमस्ते! आपका अपना बोट (Shakastor_bot) सफलतापूर्वक लाइव हो गया है।")

bot.infinity_polling()
