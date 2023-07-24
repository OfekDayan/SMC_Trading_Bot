import requests
from telethon import TelegramClient, events

BOT_ID = '5341091307:AAHGuAJDKLl3zzjIpfGhaVpW3Y3UgBNAXG4'
api_id = 18058153
api_hash = 'ad5263fdd4fc6487f1d246f01b20afa7'

telegramClient = TelegramClient('anon', api_id, api_hash)


@telegramClient.on(events.NewMessage(from_users="OfekDayan"))
async def my_event_handler(event):
    decision = event.raw_text


def send_message_to_user(message: str):
    requests.post(f'https://api.telegram.org/bot{BOT_ID}/sendMessage?chat_id=1451941685&text={message}')


telegramClient.start()
telegramClient.run_until_disconnected()