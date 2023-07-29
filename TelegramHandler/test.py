from telegram import Poll, PollOption
from telegram.ext import Updater, CommandHandler, PollHandler
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

class TelegramBot:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.updater = Updater(self.bot_token)
        self.dp = self.updater.dispatcher

        self.dp.add_handler(CommandHandler("start", self.start))
        self.dp.add_handler(CommandHandler("createpoll", self.create_poll))
        self.dp.add_handler(CommandHandler("sendimage", self.send_image_with_text))
        self.dp.add_handler(PollHandler(self.receive_poll))

    def start(self, update, context):
        update.message.reply_text("Use /createpoll to create a poll or /sendimage to send an image with text.")

    def create_poll(self, update, context):
        # Create a poll with two options
        poll_question = "Choose your option:"
        options = ["Option 1", "Option 2"]
        poll_options = [PollOption(option, count=0) for option in options]

        # Send the poll
        poll = update.message.reply_poll(question=poll_question, options=poll_options)

        # Save the poll ID for later reference
        context.user_data['poll_id'] = poll.poll.id

    def receive_poll(self, update, context):
        # Check if the received update contains a poll answer
        if update.poll_answer:
            selected_option = update.poll_answer.option_ids[0]
            options = ["Option 1", "Option 2"]
            selected_option_text = options[selected_option]
            update.message.reply_text(f"You selected: {selected_option_text}")

    def send_image_with_text(self, update, context):
        # Get the local file path and text from the user's message
        if len(context.args) < 2:
            update.message.reply_text("Usage: /sendimage <file_path> <text>")
            return

        file_path = context.args[0]
        text = " ".join(context.args[1:])

        try:
            # Open the image from the file path
            image = Image.open(file_path)

            # Add text to the image
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype("arial.ttf", 36)  # You can replace "arial.ttf" with the path to your desired font file
            draw.text((10, 10), text, fill="white", font=font)

            # Save the modified image as a byte stream
            output = BytesIO()
            image.save(output, format="PNG")
            output.seek(0)

            # Send the modified image to the user
            update.message.reply_photo(photo=output)

        except Exception as e:
            update.message.reply_text(f"An error occurred: {str(e)}")

    def start_polling(self):
        self.updater.start_polling()
        self.updater.idle()


if __name__ == "__main__":
    # Replace 'YOUR_BOT_TOKEN' with the token you received from BotFather
    bot_token = 'YOUR_BOT_TOKEN'
    bot = TelegramBot(bot_token)
    bot.start_polling()
