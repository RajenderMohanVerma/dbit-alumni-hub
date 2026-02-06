#!/usr/bin/env python
"""
Check admin credentials in database
"""

import sqlite3

DB_NAME = "alumni_hub.db"

conn = sqlite3.connect(DB_NAME)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 60)
print("Admin Users in Database")
print("=" * 60)

c.execute("SELECT id, username, email, role FROM users WHERE role='admin'")
admins = c.fetchall()

if admins:
    for admin in admins:
        print(f"\nID: {admin['id']}")
        print(f"Username: {admin['username']}")
        print(f"Email: {admin['email']}")
        print(f"Role: {admin['role']}")
else:
    print("No admin users found!")

print("\n" + "=" * 60)
print("All Users (First 10)")
print("=" * 60)

c.execute("SELECT id, username, email, role FROM users LIMIT 10")
users = c.fetchall()

for user in users:
    print(f"ID: {user['id']:3d} | Username: {user['username']:15s} | Role: {user['role']:8s}")

conn.close()
