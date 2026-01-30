import sqlite3

conn = sqlite3.connect('alumni.db')
conn.row_factory = sqlite3.Row

# Check faculty users
faculty_users = conn.execute('SELECT * FROM users WHERE role="faculty"').fetchall()
print(f"Total faculty users: {len(faculty_users)}")
for user in faculty_users:
    print(f"  - ID: {user['id']}, Name: {user['name']}, Email: {user['email']}")
    
    # Check if profile exists
    profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (user['id'],)).fetchone()
    if profile:
        print(f"    ✓ Profile exists")
    else:
        print(f"    ✗ Profile MISSING")

conn.close()
