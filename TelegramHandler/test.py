import telebot

BOT_ID = '5341091307:AAHGuAJDKLl3zzjIpfGhaVpW3Y3UgBNAXG4'
bot = telebot.TeleBot(BOT_ID)


def send_poll(chat_id, question: str, options: list[str]):
    bot.send_poll(chat_id, question, options, is_anonymous=False)


@bot.message_handler()
def start(message):
    chat_id = message.chat.id

    options = ['a', 'b', 'c']
    send_poll(chat_id, "what to do?", options)


@bot.poll_answer_handler()
def handle_poll_answer(pollAnswer):
    print(pollAnswer)


bot.infinity_polling()
