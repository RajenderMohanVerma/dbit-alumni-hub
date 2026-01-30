import sqlite3

db_file = 'college_pro.db'
conn = sqlite3.connect(db_file)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check faculty users
faculty_users = cur.execute('SELECT * FROM users WHERE role="faculty"').fetchall()
print(f'Faculty users: {len(faculty_users)}')
for user in faculty_users:
    print(f'  - {user["id"]}: {user["name"]} ({user["email"]})')
    
    # Check if profile exists
    profile = cur.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (user['id'],)).fetchone()
    if profile:
        print(f'    Profile: {profile["department"]} - {profile["designation"]}')
    else:
        print(f'    NO PROFILE')

conn.close()
