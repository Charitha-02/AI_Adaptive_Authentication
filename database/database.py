import sqlite3

# Connect to database
conn = sqlite3.connect("database/users.db")
cursor = conn.cursor()

# Create Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    face_registered INTEGER DEFAULT 0,
    keystroke_registered INTEGER DEFAULT 0
)
""")

# Create Login Logs Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS login_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT,
    login_time TEXT,
    logout_time TEXT,
    status TEXT,
    reason TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully!")