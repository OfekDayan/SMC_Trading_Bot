import requests
from telethon import TelegramClient, events

BOT_ID = '5341091307:AAHGuAJDKLl3zzjIpfGhaVpW3Y3UgBNAXG4'
api_id = 18058153
api_hash = 'ad5263fdd4fc6487f1d246f01b20afa7'
telegramClient = TelegramClient('anon', api_id, api_hash)


class TelegramHandler:
    def __init__(self):
        pass

    async def my_event_handler(self, event):
        # decision = event.raw_text
        if event.message.poll:
            self.poll_id = event.message.poll.id
            print("Poll received! Poll ID:", self.poll_id)

    # def send_message_to_user(self, message: str):
    #     requests.post(f'https://api.telegram.org/bot{BOT_ID}/sendMessage?chat_id=1451941685&text={message}')

    def send_poll_to_user(self):
        url = f'https://api.telegram.org/bot{BOT_ID}/sendPoll'
        data = {
            'chat_id': '1451941685',
            'question': 'I have a potential trade for you, what should I do?',
            'options':
                [
                    'Take the trade!',
                    'Ignore this signal',
                    'Notify me when price hits the order block',
                    'Notify me when the liquidity will be taken',
                    'Notify me if a reversal candle is found on Order Block'
                 ]
        }
        response = requests.post(url, json=data)

        if response.ok:
            poll_data = response.json()['result']
            poll_id = poll_data['poll']['id']
            return poll_id
        else:
            print(f"Failed to send poll. Status code: {response.status_code}")
            return None

    # def get_poll_response(self, poll_id):
    #     poll = await telegramClient.get_entity(poll_id)
    #     votes = await telegramClient.get_poll_votes(poll)
    #     print("Poll options and votes:")
    #     for option, count in votes.items():
    #         print(f"{option}: {count}")

    def send_message_to_user(self, message: str, image_path: str = None):
        # If image_path is provided, send photo with caption
        if image_path:
            url = f'https://api.telegram.org/bot{BOT_ID}/sendPhoto'
            data = {
                'chat_id': '1451941685',
                'caption': message
            }
            files = {'photo': open(image_path, 'rb')}
            requests.post(url, data=data, files=files)
        else:
            # Send plain text message if no image_path is provided
            url = f'https://api.telegram.org/bot{BOT_ID}/sendMessage'
            data = {
                'chat_id': '1451941685',
                'text': message
            }
            requests.post(url, data=data)

    async def start(self):
        telegramClient.add_event_handler(self.my_event_handler, events.NewMessage(from_users="OfekDayan"))
        telegramClient.start()
        telegramClient.run_until_disconnected()
