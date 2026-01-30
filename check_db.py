import sqlite3
import os

db_file = 'college_pro.db'
if not os.path.exists(db_file):
    print(f"Database file {db_file} does not exist!")
else:
    file_size = os.path.getsize(db_file)
    print(f"Database file size: {file_size} bytes")

try:
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"Found {len(tables)} tables:")
    for table in tables:
        count = cur.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
        print(f"  - {table[0]}: {count} rows")
    conn.close()
    print("\nDatabase initialized successfully!")
except Exception as e:
    print(f"Error: {e}")
