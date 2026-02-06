"""
Registration Report Generator
Generates separate CSV reports for Student, Alumni, and Faculty registrations
"""

import sqlite3
import csv
from datetime import datetime
import os

DB_NAME = 'alumni_app.db'

def get_db_connection():
    """Connect to the database"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def generate_reports():
    """Generate separate registration reports for each role"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Create reports directory if it doesn't exist
        if not os.path.exists('registration_reports'):
            os.makedirs('registration_reports')
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # ===== STUDENT REGISTRATIONS =====
        print("📚 Generating Student Registration Report...")
        c.execute('''
            SELECT 
                user_id as 'User ID',
                name as 'Full Name',
                email as 'Email',
                phone as 'Phone',
                enrollment_no as 'Enrollment No',
                department as 'Department',
                degree as 'Degree',
                registered_at as 'Registered Date'
            FROM registration_log
            WHERE role = 'student'
            ORDER BY registered_at DESC
        ''')
        
        student_data = c.fetchall()
        if student_data:
            student_file = f'registration_reports/STUDENTS_Registration_{timestamp}.csv'
            with open(student_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'User ID', 'Full Name', 'Email', 'Phone', 'Enrollment No',
                    'Department', 'Degree', 'Registered Date'
                ])
                writer.writeheader()
                for row in student_data:
                    writer.writerow(dict(row))
            print(f"✅ Student Report: {student_file} ({len(student_data)} records)")
        else:
            print("⚠️  No student registrations found")
        
        # ===== ALUMNI REGISTRATIONS =====
        print("\n🎓 Generating Alumni Registration Report...")
        c.execute('''
            SELECT 
                user_id as 'User ID',
                name as 'Full Name',
                email as 'Email',
                phone as 'Phone',
                enrollment_no as 'Enrollment No',
                department as 'Department',
                degree as 'Degree',
                pass_year as 'Passing Year',
                company_name as 'Company',
                designation as 'Designation',
                experience_years as 'Experience (Years)',
                registered_at as 'Registered Date'
            FROM registration_log
            WHERE role = 'alumni'
            ORDER BY registered_at DESC
        ''')
        
        alumni_data = c.fetchall()
        if alumni_data:
            alumni_file = f'registration_reports/ALUMNI_Registration_{timestamp}.csv'
            with open(alumni_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'User ID', 'Full Name', 'Email', 'Phone', 'Enrollment No',
                    'Department', 'Degree', 'Passing Year', 'Company', 'Designation',
                    'Experience (Years)', 'Registered Date'
                ])
                writer.writeheader()
                for row in alumni_data:
                    writer.writerow(dict(row))
            print(f"✅ Alumni Report: {alumni_file} ({len(alumni_data)} records)")
        else:
            print("⚠️  No alumni registrations found")
        
        # ===== FACULTY REGISTRATIONS =====
        print("\n👨‍🏫 Generating Faculty Registration Report...")
        c.execute('''
            SELECT 
                user_id as 'User ID',
                name as 'Full Name',
                email as 'Email',
                phone as 'Phone',
                employee_id as 'Employee ID',
                department as 'Department',
                designation as 'Designation',
                experience_years as 'Experience (Years)',
                registered_at as 'Registered Date'
            FROM registration_log
            WHERE role = 'faculty'
            ORDER BY registered_at DESC
        ''')
        
        faculty_data = c.fetchall()
        if faculty_data:
            faculty_file = f'registration_reports/FACULTY_Registration_{timestamp}.csv'
            with open(faculty_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'User ID', 'Full Name', 'Email', 'Phone', 'Employee ID',
                    'Department', 'Designation', 'Experience (Years)', 'Registered Date'
                ])
                writer.writeheader()
                for row in faculty_data:
                    writer.writerow(dict(row))
            print(f"✅ Faculty Report: {faculty_file} ({len(faculty_data)} records)")
        else:
            print("⚠️  No faculty registrations found")
        
        # ===== SUMMARY REPORT =====
        print("\n📊 Generating Summary Report...")
        c.execute('SELECT role, COUNT(*) as count FROM registration_log GROUP BY role')
        summary_data = c.fetchall()
        
        summary_file = f'registration_reports/SUMMARY_Registration_{timestamp}.csv'
        with open(summary_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Category', 'Total Registrations'])
            total = 0
            for row in summary_data:
                writer.writerow([row['role'].upper(), row['count']])
                total += row['count']
            writer.writerow(['GRAND TOTAL', total])
        
        print(f"✅ Summary Report: {summary_file}")
        
        # ===== DETAILED COMBINED REPORT =====
        print("\n📋 Generating Combined Report...")
        c.execute('''
            SELECT * FROM registration_log
            ORDER BY registered_at DESC
        ''')
        combined_data = c.fetchall()
        
        combined_file = f'registration_reports/ALL_REGISTRATIONS_{timestamp}.csv'
        if combined_data:
            with open(combined_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['User ID', 'Name', 'Email', 'Phone', 'Role', 'Enrollment/Employee No',
                            'Department', 'Degree', 'Pass Year', 'Company', 'Designation',
                            'Experience (Years)', 'Registered Date']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in combined_data:
                    writer.writerow({
                        'User ID': row['user_id'],
                        'Name': row['name'],
                        'Email': row['email'],
                        'Phone': row['phone'],
                        'Role': row['role'].upper(),
                        'Enrollment/Employee No': row['enrollment_no'] or row['employee_id'] or '',
                        'Department': row['department'] or '',
                        'Degree': row['degree'] or '',
                        'Pass Year': row['pass_year'] or '',
                        'Company': row['company_name'] or '',
                        'Designation': row['designation'] or '',
                        'Experience (Years)': row['experience_years'] or '',
                        'Registered Date': row['registered_at']
                    })
            print(f"✅ Combined Report: {combined_file} ({len(combined_data)} records)")
        
        conn.close()
        
        print("\n" + "="*60)
        print("✨ All registration reports generated successfully!")
        print("📁 Location: registration_reports/")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error generating reports: {e}")

if __name__ == '__main__':
    generate_reports()
