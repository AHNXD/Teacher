import os
import cv2
from pyzbar import pyzbar
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Replace with your bot token
BOT_TOKEN = "7689649103:AAEkOak9caU-obULdGqU0DTmkQZhNuZIRis"

# Database to store phone numbers and chat IDs
user_db = {}

# List of links for students
STUDENT_LINKS = [
    {"name": "Google", "url": "https://www.google.com"},
    {"name": "GitHub", "url": "https://www.github.com"},
    {"name": "YouTube", "url": "https://www.youtube.com"},
]

# Command to show links to students
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton(link["name"], url=link["url"])] for link in STUDENT_LINKS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Here are the links:", reply_markup=reply_markup)

    # Ask the user to provide their phone number
    await update.message.reply_text("Please send your phone number in the format +1234567890.")

# Handle phone number input from users
async def handle_phone_number(update: Update, context: CallbackContext):
    phone_number = update.message.text
    chat_id = update.message.chat_id

    # Validate the phone number format
    if phone_number[:].isdigit():
        # Store the phone number and chat ID in the database
        user_db[phone_number] = chat_id
        await update.message.reply_text(f"Thank you! Your phone number {phone_number} has been registered.")
    else:
        await update.message.reply_text("Invalid phone number format. Please send your phone number in the format +1234567890.")

# Function to decode QR code
def decode_qr_code(image_path):
    image = cv2.imread(image_path)
    decoded_objects = pyzbar.decode(image)
    for obj in decoded_objects:
        return obj.data.decode("utf-8")
    return None

# Handle QR code images sent by admin
async def handle_qr_code(update: Update, context: CallbackContext):
    user = update.message.from_user
    if user.username == "AHNXD":  # Replace with your admin's username
        file = await update.message.photo[-1].get_file()
        file_path = f"qr_code_{update.message.message_id}.jpg"
        await file.download_to_drive(file_path)

        qr_data = decode_qr_code(file_path)
        if qr_data:
            try:
                # Check if the phone number is in the database
                if qr_data in user_db:
                    chat_id = user_db[qr_data]
                    await update.message.reply_text(f"QR code decoded: {qr_data}")
                    await context.bot.send_message(chat_id=chat_id, text="Hello, I am your bot!")
                else:
                    await update.message.reply_text(f"No user found with phone number {qr_data}.")
            except Exception as e:
                await update.message.reply_text(f"Failed to send message: {e}")
        else:
            await update.message.reply_text("No QR code found in the image.")

        os.remove(file_path)  # Clean up the downloaded file
    else:
        await update.message.reply_text("You are not authorized to send QR codes.")

# Main function to run the bot
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_number))
    application.add_handler(MessageHandler(filters.PHOTO, handle_qr_code))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()