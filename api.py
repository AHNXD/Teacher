from fastapi import FastAPI, HTTPException
import threading
import sqlite3
import uvicorn
from pydantic import BaseModel
from bot import main as run_bot

# Define Pydantic models for request bodies
class AdminCreate(BaseModel):
    username: str

class LinkCreate(BaseModel):
    name: str
    url: str

class UserCreate(BaseModel):
    phone_number: str
    chat_id: int

# Initialize FastAPI app
app = FastAPI()

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

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
# Run the FastAPI app
if __name__ == "__main__":
    
    api_thread = threading.Thread(target=run_fastapi)
    api_thread.start()

    # Run the Telegram bot in the main thread
    run_bot()