import telebot

BOT_ID = '5341091307:AAHGuAJDKLl3zzjIpfGhaVpW3Y3UgBNAXG4'
bot = telebot.TeleBot(BOT_ID)


def send_poll(chat_id, question: str, options: list[str]):
    bot.send_poll(chat_id, question, options, is_anonymous=False)


def send_image(chat_id, image_path: str, caption: str = None):
    with open(image_path, 'rb') as image_file:
        bot.send_photo(chat_id, image_file, caption)


@bot.message_handler()
def start(message):
    chat_id = message.chat.id

    send_signal(chat_id, "C:\\Users\\ofekbiny\\Downloads\\newplot.png")


def send_signal(chat_id, image_path: str):
    send_image(chat_id, image_path, "")

    options = ['Take the trade!',
               'Ignore this signal',
               'Notify me when price hits the order block',
               'Notify me when the liquidity will be taken',
               'Notify me if a reversal candle is found on Order Block']
    send_poll(chat_id, "what to do?", options)


@bot.poll_answer_handler()
def handle_poll_answer(pollAnswer):
    print(pollAnswer)


bot.infinity_polling()
