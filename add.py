import sqlite3

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

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('bot_data.db')
cursor = conn.cursor()

# Insert initial social links
social_links = [
    {"name": "Google", "url": "https://www.google.com"},
    {"name": "GitHub", "url": "https://www.github.com"},
    {"name": "YouTube", "url": "https://www.youtube.com"},
]

cursor.executemany('INSERT INTO social_links (name, url) VALUES (:name, :url)', social_links)

# Insert initial admins
admins = [
    {"username": "AHNXD"},  # Replace with your admin's username
]

cursor.executemany('INSERT INTO admins (username) VALUES (:username)', admins)

# # Insert initial users (phone numbers and chat IDs)
# users = [
#     {"phone_number": "+1234567890", "chat_id": 123456789},  # Replace with actual data
#     {"phone_number": "+9876543210", "chat_id": 987654321},  # Replace with actual data
# ]

# cursor.executemany('INSERT INTO users (phone_number, chat_id) VALUES (:phone_number, :chat_id)', users)

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database populated successfully!")