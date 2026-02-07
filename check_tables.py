import sqlite3

conn = sqlite3.connect('college_pro.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print("All tables in database:")
for t in tables:
    print(f"  - {t[0]}")

# Check for profile-related tables
print("\nLooking for profile tables:")
for table in tables:
    if 'profile' in table[0].lower():
        print(f"  Found: {table[0]}")
        cursor.execute(f"PRAGMA table_info({table[0]})")
        print(f"    Columns: {[col[1] for col in cursor.fetchall()]}")

conn.close()
