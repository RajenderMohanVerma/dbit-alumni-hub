import sqlite3

conn = sqlite3.connect('college_pro.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Available tables:")
for t in tables:
    print(f"  - {t[0]}")

# Check faculty_profile table
print("\nFaculty Profile Schema:")
try:
    cursor.execute("PRAGMA table_info(faculty_profile)")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    cursor.execute("SELECT COUNT(*) FROM faculty_profile")
    print(f"\nTotal faculty profiles: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"Error: {e}")

# Check users table for faculty
cursor.execute("SELECT COUNT(*) FROM users WHERE role='faculty'")
print(f"Total faculty users: {cursor.fetchone()[0]}")

conn.close()
