import os
import cv2
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import asyncio

# --- FastAPI Section ---
app = FastAPI()

# Pydantic models (same as before)
class AdminCreate(BaseModel):
    username: str

class LinkCreate(BaseModel):
    name: str
    url: str

class UserCreate(BaseModel):
    phone_number: str
    chat_id: int

# Database connection helper (same as before)
def get_db_connection():
    conn = sqlite3.connect('bot_data.db')
    conn.row_factory = sqlite3.Row
    return conn

# FastAPI endpoints (same as before)
@app.post("/admins/")
def add_admin(admin: AdminCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO admins (username) VALUES (?)', (admin.username,))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Admin already exists")
    finally:
        conn.close()
    
    return {"message": f"Admin {admin.username} added successfully"}

@app.post("/links/")
def add_link(link: LinkCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO social_links (name, url) VALUES (?, ?)', (link.name, link.url))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Link already exists")
    finally:
        conn.close()
    
    return {"message": f"Link {link.name} added successfully"}

@app.post("/users/")
def add_user(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO users (phone_number, chat_id) VALUES (?, ?)', (user.phone_number, user.chat_id))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        conn.close()
    
    return {"message": f"User {user.phone_number} added successfully"}

# --- Telegram Bot Section ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
URL = os.getenv("URL")

# Initialize the database (same as before)
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
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

init_db()

# Function to create an inline keyboard with a "Show Links" button
def create_links_keyboard():
    keyboard = [
        [InlineKeyboardButton("Show Links", callback_data="show_links")]
    ]
    return InlineKeyboardMarkup(keyboard)


# Telegram bot functions (mostly the same, with modifications)
async def start(update: Update, context: CallbackContext):
    # Send a welcome message with the "Show Links" button
    reply_markup = create_links_keyboard()
    await update.message.reply_text(
        "Welcome! Use the button below to show the links.",
        reply_markup=reply_markup
    )

    # Ask the user to provide their phone number
    await update.message.reply_text("Please send your phone number in the format 09xxxxxxxx.")


async def show_links_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    # Fetch links from the database
    cursor.execute('SELECT name, url FROM social_links')
    links = cursor.fetchall()
    
    # Create inline buttons for each link
    keyboard = [
        [InlineKeyboardButton(link[0], url=link[1])] for link in links
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send the links to the user
    await query.edit_message_text("Here are the links:", reply_markup=reply_markup)
    
    conn.close()

async def handle_phone_number(update: Update, context: CallbackContext):
    phone_number = update.message.text
    chat_id = update.message.chat_id

    if phone_number[:].isdigit():
        # Use FastAPI endpoint to add user
        try:
            # Make an asynchronous HTTP request to FastAPI
            import aiohttp  # Import aiohttp inside the function
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{URL}/users/", json={"phone_number": phone_number, "chat_id": chat_id}) as resp:
                    if resp.status == 200:
                        await update.message.reply_text(f"Thank you! Your phone number {phone_number} has been registered.")
                    else:
                        error_data = await resp.json()
                        await update.message.reply_text(f"Error registering: {error_data.get('detail', 'Unknown error')}")
        except Exception as e:
            await update.message.reply_text(f"Error registering: {e}")
    else:
        await update.message.reply_text("Invalid phone number format. Please send your phone number in the format 09xxxxxxxx.")

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

# --- Combined Main Function ---
async def telegram_main():  # Make this an async function
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers (same as before)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_links_callback, pattern="^show_links$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_number))
    application.add_handler(MessageHandler(filters.PHOTO, handle_qr_code))

    await application.initialize() # Initialize the application
    await application.start_polling()  # Use start_polling for local development
    await application.idle()


async def fastapi_main():  # Make this an async function
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config=config)
    await server.serve()


async def main():
    # Run both Telegram bot and FastAPI concurrently
    await asyncio.gather(telegram_main(), fastapi_main())

if __name__ == "__main__":
    asyncio.run(main()) # Use asyncio.run to start the async main function