import sqlite3
import os
from werkzeug.security import generate_password_hash

# Remove old database
if os.path.exists('alumni.db'):
    os.remove('alumni.db')

DB_NAME = 'alumni.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

# Initialize database
conn = None
try:
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            role TEXT NOT NULL,
            profile_pic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS faculty_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            employee_id TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            specialization TEXT,
            qualification TEXT,
            experience_years INTEGER,
            office_location TEXT,
            office_hours TEXT,
            bio TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create admin
    pw = generate_password_hash("admin123")
    c.execute("INSERT INTO users (name, email, password, role, phone) VALUES (?, ?, ?, ?, ?)",
              ("Super Admin", "admin@college.edu", pw, "admin", "0000000000"))
    
    conn.commit()
    print("Database created and committed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    if conn:
        conn.rollback()
finally:
    if conn:
        conn.close()

# Verify
print("\nVerifying database...")
conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"Tables: {[t[0] for t in tables]}")
users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
print(f"Users: {users}")
conn.close()
