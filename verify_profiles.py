#!/usr/bin/env python3
import sqlite3

DB_FILE = 'college_pro.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def main():
    conn = get_db_connection()
    
    print("=" * 80)
    print("CHECKING ALL USERS AND THEIR PROFILES")
    print("=" * 80)
    
    # Get all users
    users = conn.execute('SELECT id, name, email, role FROM users ORDER BY role, id').fetchall()
    
    for user in users:
        user_id = user['id']
        name = user['name']
        email = user['email']
        role = user['role']
        
        print(f"\n[User {user_id}] {name} ({role}) - {email}")
        
        if role == 'student':
            profile = conn.execute('SELECT * FROM student_profile WHERE user_id = ?', (user_id,)).fetchone()
            if profile:
                print(f"  ✓ Has STUDENT profile - Semester: {profile['semester']}, Department: {profile['department']}, CGPA: {profile['cgpa']}")
            else:
                print(f"  ✗ MISSING STUDENT profile - NEEDS TO BE CREATED")
                
        elif role == 'alumni':
            profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (user_id,)).fetchone()
            if profile:
                print(f"  ✓ Has ALUMNI profile - Company: {profile['company_name']}, Designation: {profile['designation']}")
            else:
                print(f"  ✗ MISSING ALUMNI profile - NEEDS TO BE CREATED")
                
        elif role == 'faculty':
            profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (user_id,)).fetchone()
            if profile:
                print(f"  ✓ Has FACULTY profile - Designation: {profile['designation']}, Department: {profile['department']}")
            else:
                print(f"  ✗ MISSING FACULTY profile")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    students_count = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = ?', ('student',)).fetchone()['count']
    students_with_profile = conn.execute('SELECT COUNT(*) as count FROM student_profile').fetchone()['count']
    
    alumni_count = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = ?', ('alumni',)).fetchone()['count']
    alumni_with_profile = conn.execute('SELECT COUNT(*) as count FROM alumni_profile').fetchone()['count']
    
    faculty_count = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = ?', ('faculty',)).fetchone()['count']
    faculty_with_profile = conn.execute('SELECT COUNT(*) as count FROM faculty_profile').fetchone()['count']
    
    print(f"Students: {students_with_profile}/{students_count} have profiles")
    print(f"Alumni: {alumni_with_profile}/{alumni_count} have profiles")
    print(f"Faculty: {faculty_with_profile}/{faculty_count} have profiles")
    
    conn.close()

if __name__ == '__main__':
    main()
