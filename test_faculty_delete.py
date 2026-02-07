import sqlite3
import sys

# Test deleting a faculty member
conn = sqlite3.connect('college_pro.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get a faculty user
cursor.execute("SELECT * FROM users WHERE role='faculty' LIMIT 1")
faculty = cursor.fetchone()

if not faculty:
    print("No faculty found in database")
    sys.exit(0)

user_id = faculty['id']
print(f"Testing deletion for Faculty ID: {user_id}")
print(f"Name: {faculty['name']}, Email: {faculty['email']}")

# Try to delete from faculty_profile
try:
    cursor.execute("DELETE FROM faculty_profile WHERE user_id = ?", (user_id,))
    print(f"✓ Successfully deleted from faculty_profile (rows affected: {cursor.rowcount})")
except Exception as e:
    print(f"✗ Error deleting from faculty_profile: {e}")

# Check if there are any foreign key constraints
cursor.execute("PRAGMA foreign_keys")
fk_status = cursor.fetchone()
print(f"\nForeign keys enabled: {fk_status[0] if fk_status else 'Unknown'}")

# Check faculty_profile structure
cursor.execute("PRAGMA table_info(faculty_profile)")
print("\nFaculty Profile columns:")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

# Rollback changes
conn.rollback()
conn.close()
print("\n(Changes rolled back - no actual deletion)")
