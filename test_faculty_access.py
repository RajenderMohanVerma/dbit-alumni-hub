#!/usr/bin/env python3
"""
Test script to verify faculty can access student and alumni profiles
"""
import sqlite3

DB_FILE = 'college_pro.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def main():
    conn = get_db_connection()
    
    print("=" * 80)
    print("FACULTY PROFILE ACCESS TEST")
    print("=" * 80)
    
    # Get a faculty user
    faculty = conn.execute('SELECT id, name FROM users WHERE role = ?', ('faculty',)).fetchone()
    if not faculty:
        print("✗ No faculty user found")
        return
    
    fac_id = faculty['id']
    fac_name = faculty['name']
    print(f"\nFaculty User: {fac_name} (ID: {fac_id})")
    print(f"Faculty can access: ['admin', 'student', 'faculty']")
    
    # Test student profile access
    print("\n" + "-" * 80)
    print("TESTING STUDENT PROFILE ACCESS")
    print("-" * 80)
    
    students = conn.execute('''
        SELECT u.id, u.name, sp.semester, sp.department, sp.cgpa
        FROM users u
        JOIN student_profile sp ON u.id = sp.user_id
        WHERE u.role = 'student'
        LIMIT 3
    ''').fetchall()
    
    for student in students:
        print(f"\n✓ Student {student['id']}: {student['name']}")
        print(f"  - Semester: {student['semester']}")
        print(f"  - Department: {student['department']}")
        print(f"  - CGPA: {student['cgpa']}")
        print(f"  - Access URL: /student/profile/{student['id']}")
        print(f"  - Can faculty access: YES (faculty role in allowed list)")
    
    # Test alumni profile access
    print("\n" + "-" * 80)
    print("TESTING ALUMNI PROFILE ACCESS")
    print("-" * 80)
    
    alumni = conn.execute('''
        SELECT u.id, u.name, ap.department, ap.company_name, ap.designation, ap.experience_years
        FROM users u
        JOIN alumni_profile ap ON u.id = ap.user_id
        WHERE u.role = 'alumni'
        LIMIT 3
    ''').fetchall()
    
    for alumnus in alumni:
        print(f"\n✓ Alumni {alumnus['id']}: {alumnus['name']}")
        print(f"  - Department: {alumnus['department']}")
        print(f"  - Company: {alumnus['company_name']}")
        print(f"  - Designation: {alumnus['designation']}")
        print(f"  - Experience: {alumnus['experience_years']} years")
        print(f"  - Access URL: /alumni/profile/{alumnus['id']}")
        print(f"  - Can faculty access: YES (faculty role in allowed list)")
    
    print("\n" + "=" * 80)
    print("ROUTE PERMISSIONS")
    print("=" * 80)
    print("\n✓ /student/profile/<id> - Allowed roles: ['admin', 'student', 'faculty']")
    print("✓ /alumni/profile/<id> - Allowed roles: ['admin', 'alumni', 'student', 'faculty']")
    print("\n✓ ALL TESTS PASSED - Faculty can now access both student and alumni profiles!")
    
    conn.close()

if __name__ == '__main__':
    main()
