import os
import cv2
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Replace with your bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Database setup
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            phone_number TEXT PRIMARY KEY,
            chat_id INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS social_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            username TEXT PRIMARY KEY
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()


# Command to show links to students
async def start(update: Update, context: CallbackContext):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT name, url FROM social_links')
    links = cursor.fetchall()
    
    keyboard = [
        [InlineKeyboardButton(link[0], url=link[1])] for link in links
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Here are the links:", reply_markup=reply_markup)

    # Ask the user to provide their phone number
    await update.message.reply_text("Please send your phone number in the format 09xxxxxxxx.")
    
    conn.close()
    
# Command to show links to students
async def show_links(update: Update, context: CallbackContext):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT name, url FROM social_links')
    links = cursor.fetchall()
    
    keyboard = [
        [InlineKeyboardButton(link[0], url=link[1])] for link in links
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Here are the links:", reply_markup=reply_markup)

    # Ask the user to provide their phone number
    await update.message.reply_text("Please send your phone number in the format 09xxxxxxxx.")
    
    conn.close()

# Handle phone number input from users
async def handle_phone_number(update: Update, context: CallbackContext):
    phone_number = update.message.text
    chat_id = update.message.chat_id

    # Validate the phone number format
    if phone_number[:].isdigit():
        # Store the phone number and chat ID in the database
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        # Store the phone number and chat ID in the database
        cursor.execute('INSERT OR REPLACE INTO users (phone_number, chat_id) VALUES (?, ?)', (phone_number, chat_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"Thank you! Your phone number {phone_number} has been registered.")
    else:
        await update.message.reply_text("Invalid phone number format. Please send your phone number in the format +1234567890.")

def decode_qr_code(image_path):
    img = cv2.imread(image_path)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    return data

# Handle QR code images sent by admin
async def handle_qr_code(update: Update, context: CallbackContext):
    user = update.message.from_user
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT username FROM admins WHERE username = ?', (user.username,))
    admin = cursor.fetchone()
    
    if admin:  # Replace with your admin's username
        file = await update.message.photo[-1].get_file()
        file_path = f"qr_code_{update.message.message_id}.jpg"
        await file.download_to_drive(file_path)

        qr_data = decode_qr_code(file_path)
        if qr_data:
            try:
                # Check if the phone number is in the database
                if qr_data:
                    cursor.execute('SELECT chat_id FROM users WHERE phone_number = ?', (qr_data,))
                    user_data = cursor.fetchone()
                    if user_data:
                        chat_id = user_data[0]
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
    conn.close()

# Main function to run the bot
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("Show Links", show_links))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_number))
    application.add_handler(MessageHandler(filters.PHOTO, handle_qr_code))

    # Set up webhook
    application.run_webhook(
        listen="0.0.0.0",  # Bind to all available interfaces
        port=8080,         # Use port 8080
        url_path="",       # No URL path
        webhook_url= os.getenv("URL")  # Replace with your Render URL
    )

if __name__ == "__main__":
    main()