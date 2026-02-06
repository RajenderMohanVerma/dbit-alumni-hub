#!/usr/bin/env python3
"""Verify that the Connection Request System is fully implemented"""

import sqlite3
from app import app, init_db, get_db_connection

print("\n" + "="*60)
print("🔍 VERIFYING UNIFIED CONNECTION REQUEST SYSTEM")
print("="*60)

# Initialize database
print("\n1️⃣  Initializing database...")
init_db()
print("   ✅ Database initialized")

# Check tables
print("\n2️⃣  Checking database tables...")
conn = get_db_connection()
c = conn.cursor()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
required_tables = ['users', 'connection_requests', 'connections', 'student_profile', 'alumni_profile', 'faculty_profile']
existing_tables = [t[0] for t in tables]

for table in required_tables:
    if table in existing_tables:
        print(f"   ✅ {table}")
    else:
        print(f"   ❌ {table} - MISSING!")

conn.close()

# Check API endpoints
print("\n3️⃣  Checking API endpoints...")
endpoints = [
    ('POST', '/api/connection-request/send'),
    ('POST', '/api/connection-request/accept/<sender_id>'),
    ('POST', '/api/connection-request/reject/<sender_id>'),
    ('GET', '/api/connection-request/status/<user_id>'),
    ('GET', '/api/connection-requests/pending'),
]

for method, path in endpoints:
    found = False
    for rule in app.url_map.iter_rules():
        if rule.rule == path and method in rule.methods:
            found = True
            break
    if found:
        print(f"   ✅ {method} {path}")
    else:
        print(f"   ❌ {method} {path} - MISSING!")

# Check functions
print("\n4️⃣  Checking key functions...")
functions = [
    'send_connection_request',
    'accept_connection_request', 
    'reject_connection_request',
    'get_connection_status',
    'get_pending_connection_requests',
    'send_connection_email'
]

import inspect
source = inspect.getsource(app)
for func in functions:
    if f'def {func}' in source:
        print(f"   ✅ {func}()")
    else:
        print(f"   ❌ {func}() - NOT FOUND!")

# Check templates
print("\n5️⃣  Checking dashboard templates...")
import os
templates = [
    'templates/dashboard_student.html',
    'templates/dashboard_alumni.html',
    'templates/dashboard_faculty.html'
]

for template in templates:
    if os.path.exists(template):
        # Check if it has connection request code
        with open(template, 'r') as f:
            content = f.read()
            if 'connection' in content.lower():
                print(f"   ✅ {template} (has connection code)")
            else:
                print(f"   ⚠️  {template} (no connection code found)")
    else:
        print(f"   ❌ {template} - NOT FOUND!")

print("\n" + "="*60)
print("✨ VERIFICATION COMPLETE!")
print("="*60 + "\n")
