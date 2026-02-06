from app import get_db_connection, init_db
import sqlite3

print("Initializing database...")
init_db()

print("\nChecking tables...")
conn = get_db_connection()
c = conn.cursor()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"Found {len(tables)} tables:")
for t in tables:
    print(f"  - {t[0]}")

# Check specific tables
try:
    c.execute("SELECT COUNT(*) FROM users")
    print("\n✅ users table exists")
except Exception as e:
    print(f"\n❌ users table error: {e}")

try:
    c.execute("SELECT COUNT(*) FROM connection_requests")
    print("✅ connection_requests table exists")
except Exception as e:
    print(f"❌ connection_requests table error: {e}")

try:
    c.execute("SELECT COUNT(*) FROM connections")
    print("✅ connections table exists")
except Exception as e:
    print(f"❌ connections table error: {e}")

conn.close()
