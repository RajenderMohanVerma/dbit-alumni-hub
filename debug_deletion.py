import sqlite3
import os
from config import DevelopmentConfig

db_name = DevelopmentConfig.DB_NAME

print(f"📍 Using database: {db_name}")
print(f"📍 Database exists: {os.path.exists(db_name)}")

if not os.path.exists(db_name):
    print("❌ Database file not found!")
    exit(1)

conn = sqlite3.connect(db_name)
c = conn.cursor()

# Check faculty_profile schema
print("\n📋 Faculty Profile Table Schema:")
try:
    schema = c.execute("PRAGMA table_info(faculty_profile)").fetchall()
    if schema:
        for col in schema:
            print(f"   {col[1]} ({col[2]}) - PK: {col[5]}")
    else:
        print("   ❌ Faculty profile table does not exist!")
except Exception as e:
    print(f"   Error: {e}")

print("\n📋 Checking Foreign Keys for faculty_profile:")
try:
    fks = c.execute("PRAGMA foreign_key_list(faculty_profile)").fetchall()
    if fks:
        for fk in fks:
            print(f"   References {fk[2]}.{fk[4]} <- {fk[3]}")
    else:
        print("   No foreign key constraints found")
except Exception as e:
    print(f"   Error: {e}")

# Check if there are any faculty users
print("\n👥 Faculty Users Count:")
try:
    faculty_count = c.execute("SELECT COUNT(*) FROM users WHERE role='faculty'").fetchone()[0]
    print(f"   Total faculty users: {faculty_count}")
except Exception as e:
    print(f"   Error: {e}")

# Check if faculty profiles exist
print("\n📝 Faculty Profiles Count:")
try:
    profiles_count = c.execute("SELECT COUNT(*) FROM faculty_profile").fetchone()[0]
    print(f"   Total faculty profiles: {profiles_count}")
except Exception as e:
    print(f"   Error: {e}")

# List all faculty users and their profiles
try:
    faculty_count = c.execute("SELECT COUNT(*) FROM users WHERE role='faculty'").fetchone()[0]
    if faculty_count > 0:
        print("\n📄 Faculty Users and Profiles:")
        faculty_users = c.execute("SELECT id, name, email FROM users WHERE role='faculty'").fetchall()
        for user in faculty_users:
            try:
                profile = c.execute("SELECT id FROM faculty_profile WHERE user_id = ?", (user[0],)).fetchone()
                if profile:
                    print(f"   ✓ ID {user[0]}: {user[1]} ({user[2]}) - Has Profile")
                else:
                    print(f"   ✗ ID {user[0]}: {user[1]} ({user[2]}) - NO Profile")
            except Exception as e:
                print(f"   Error checking profile for user {user[0]}: {e}")
except Exception as e:
    print(f"   Error: {e}")

# Check other tables that might reference faculty_profile
print("\n🔗 Checking all tables that might reference user_id:")
try:
    tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for table in tables:
        table_name = table[0]
        if table_name in ['sqlite_sequence']:
            continue
        try:
            cols = c.execute(f"PRAGMA table_info({table_name})").fetchall()
            for col in cols:
                if 'user_id' in col[1]:
                    count = c.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    print(f"   • {table_name}.{col[1]} (Total rows: {count})")
        except Exception as e:
            print(f"   Error checking table {table_name}: {e}")
except Exception as e:
    print(f"   Error: {e}")

conn.close()
