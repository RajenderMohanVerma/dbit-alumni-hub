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
    print("CREATING MISSING PROFILES")
    print("=" * 80)
    
    # Create missing student profiles
    students = conn.execute('''
        SELECT u.id, u.name FROM users u
        WHERE u.role = 'student' 
        AND u.id NOT IN (SELECT user_id FROM student_profile)
    ''').fetchall()
    
    for student in students:
        user_id = student['id']
        name = student['name']
        try:
            conn.execute('''
                INSERT INTO student_profile 
                (user_id, enrollment_no, degree, semester, department, cgpa, skills)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, f'ENR{user_id}', 'BCA', 1, 'BCA', 0.0, ''))
            print(f"✓ Created student profile for {name} (ID: {user_id})")
        except Exception as e:
            print(f"✗ Error creating student profile for {name}: {e}")
    
    # Create missing alumni profiles
    alumni = conn.execute('''
        SELECT u.id, u.name FROM users u
        WHERE u.role = 'alumni' 
        AND u.id NOT IN (SELECT user_id FROM alumni_profile)
    ''').fetchall()
    
    for alumnus in alumni:
        user_id = alumnus['id']
        name = alumnus['name']
        try:
            conn.execute('''
                INSERT INTO alumni_profile 
                (user_id, enrollment_no, degree, pass_year, department, company_name, designation, work_location, experience_years, bio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, f'ENR{user_id}', 'BCA', 2020, 'BCA', 'Not Specified', 'Not Specified', 'India', 2, ''))
            print(f"✓ Created alumni profile for {name} (ID: {user_id})")
        except Exception as e:
            print(f"✗ Error creating alumni profile for {name}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 80)
    print("PROFILE CREATION COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
