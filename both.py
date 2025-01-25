import os
import threading
import asyncio
from fastapi import FastAPI, HTTPException
import sqlite3
from pydantic import BaseModel
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler

# Replace with your bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize FastAPI app
app = FastAPI()

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

# Define Pydantic models for request bodies
class AdminCreate(BaseModel):
    username: str

class LinkCreate(BaseModel):
    name: str
    url: str

class UserCreate(BaseModel):
    phone_number: str
    chat_id: int

# Database connection helper function
def get_db_connection():
    conn = sqlite3.connect('bot_data.db')
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

# Endpoint to add a new admin
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

# Endpoint to add a new social link
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

# Endpoint to add a new user
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

# Telegram bot logic
def run_bot():
    # Create a new event loop for the bot thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    application = Application.builder().token(BOT_TOKEN).build()

    # Function to create an inline keyboard with a "Show Links" button
    def create_links_keyboard():
        keyboard = [
            [InlineKeyboardButton("Show Links", callback_data="show_links")]
        ]
        return InlineKeyboardMarkup(keyboard)

    # Command to start the bot
    async def start(update: Update, context: CallbackContext):
        reply_markup = create_links_keyboard()
        await update.message.reply_text(
            "Welcome! Use the button below to show the links.",
            reply_markup=reply_markup
        )
        await update.message.reply_text("Please send your phone number in the format 09xxxxxxxx.")

    # Callback query handler for the "Show Links" button
    async def show_links_callback(update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()  # Acknowledge the callback query

        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT name, url FROM social_links')
        links = cursor.fetchall()
        
        keyboard = [
            [InlineKeyboardButton(link[0], url=link[1])] for link in links
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text("Here are the links:", reply_markup=reply_markup)
        
        conn.close()

    # Handle phone number input from users
    async def handle_phone_number(update: Update, context: CallbackContext):
        phone_number = update.message.text
        chat_id = update.message.chat_id

        if phone_number[:].isdigit():
            conn = sqlite3.connect('bot_data.db')
            cursor = conn.cursor()
            
            cursor.execute('INSERT OR REPLACE INTO users (phone_number, chat_id) VALUES (?, ?)', (phone_number, chat_id))
            conn.commit()
            conn.close()
            await update.message.reply_text(f"Thank you! Your phone number {phone_number} has been registered.")
        else:
            await update.message.reply_text("Invalid phone number format. Please send your phone number in the format 09xxxxxxxx.")

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(show_links_callback, pattern="^show_links$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_number))

    # Start the bot
    application.run_polling()

# Start the bot in a separate thread
bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)