from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from config import config
import time
import base64
from datetime import datetime

app = Flask(__name__)
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

DB_NAME = app.config['DB_NAME']

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- LOGIN SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, name, email, role, profile_pic):
        self.id = id
        self.name = name
        self.email = email
        self.role = role
        self.profile_pic = profile_pic

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        # Avatar generation logic
        avatar = user['profile_pic'] if user['profile_pic'] else f"https://ui-avatars.com/api/?name={user['name']}&background=0D6EFD&color=fff"
        return User(user['id'], user['name'], user['email'], user['role'], avatar)
    return None

# --- DATABASE SETUP ---
def init_db():
    """Initialize the database with all required tables"""
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT,
                role TEXT NOT NULL,
                profile_pic TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Student Profile Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS student_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                enrollment_no TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                degree TEXT NOT NULL,
                semester INTEGER,
                cgpa REAL,
                skills TEXT,
                achievements TEXT,
                resume_link TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Alumni Profile Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS alumni_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                enrollment_no TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                degree TEXT NOT NULL,
                pass_year INTEGER NOT NULL,
                company_name TEXT,
                designation TEXT,
                work_location TEXT,
                experience_years INTEGER,
                linkedin_url TEXT,
                achievements TEXT,
                bio TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Faculty Profile Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS faculty_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                employee_id TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                designation TEXT NOT NULL,
                specialization TEXT,
                qualification TEXT,
                experience_years INTEGER,
                office_location TEXT,
                office_hours TEXT,
                bio TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Alumni Meet Registration Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS alumni_meet_registration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                gender TEXT,
                dob TEXT,
                contact_no TEXT NOT NULL,
                email TEXT NOT NULL,
                current_address TEXT,
                enrollment_no TEXT NOT NULL,
                course TEXT NOT NULL,
                passing_year INTEGER,
                current_status TEXT,
                company_name TEXT,
                designation TEXT,
                work_location TEXT,
                experience_years INTEGER,
                university_name TEXT,
                higher_study_course TEXT,
                higher_study_country TEXT,
                higher_study_state TEXT,
                enrollment_year INTEGER,
                contribute_to_college TEXT,
                contribution_areas TEXT,
                attending_meet TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Check if admin exists
        admin_exists = c.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
        
        # Create Admin if not exists
        if admin_exists == 0:
            pw = generate_password_hash("admin123")
            c.execute("INSERT INTO users (name, email, password, role, phone) VALUES (?, ?, ?, ?, ?)",
                      ("Super Admin", "admin@college.edu", pw, "admin", "0000000000"))
        
        conn.commit()
        print("Database initialized successfully!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Initialization error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()

            if not all([name, email, subject, message]):
                flash('All fields are required!', 'warning')
                return render_template('contact.html')

            flash('Thank you! We will get back to you soon.', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            flash('Error sending message. Please try again.', 'danger')
    
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = None
        try:
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            
            if user and check_password_hash(user['password'], password):
                user_obj = User(user['id'], user['name'], user['email'], user['role'], None)
                login_user(user_obj)
                if user['role'] == 'admin': 
                    return redirect(url_for('dashboard_admin'))
                if user['role'] == 'alumni': 
                    return redirect(url_for('dashboard_alumni'))
                return redirect(url_for('dashboard_student'))
            else:
                flash('Invalid Email or Password', 'danger')
        finally:
            if conn:
                conn.close()
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    role = request.args.get('role', 'student')
    
    if request.method == 'POST':
        conn = None
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', '')
            role = request.form.get('role', 'student')
            
            if not name or not email or not phone or not password:
                flash('Name, Email, Phone, and Password are required!', 'warning')
                return redirect(url_for('register', role=role))
            
            password_hash = generate_password_hash(password)
            
            conn = get_db_connection()
            c = conn.cursor()
            
            # Insert user
            c.execute('INSERT INTO users (name, email, password, phone, role) VALUES (?, ?, ?, ?, ?)',
                     (name, email, password_hash, phone, role))
            conn.commit()
            
            user_id = c.lastrowid
            
            # Role-specific data insertion
            if role == 'student':
                enrollment_no = request.form.get('enrollment_no', '').strip()
                department = request.form.get('department', '').strip()
                degree = request.form.get('degree', '').strip()
                semester = request.form.get('semester', '')
                
                if not all([enrollment_no, department, degree]):
                    flash('Student details are incomplete!', 'warning')
                    return redirect(url_for('register', role='student'))
                
                c.execute('''INSERT INTO student_profile 
                    (user_id, enrollment_no, department, degree, semester)
                    VALUES (?, ?, ?, ?, ?)''',
                    (user_id, enrollment_no, department, degree, semester))
            
            elif role == 'alumni':
                enrollment_no = request.form.get('enrollment_no', '').strip()
                department = request.form.get('department', '').strip()
                degree = request.form.get('degree', '').strip()
                pass_year = request.form.get('pass_year', '')
                company_name = request.form.get('company_name', '')
                designation = request.form.get('designation', '')
                
                if not all([enrollment_no, department, degree, pass_year]):
                    flash('Alumni details are incomplete!', 'warning')
                    return redirect(url_for('register', role='alumni'))
                
                c.execute('''INSERT INTO alumni_profile 
                    (user_id, enrollment_no, department, degree, pass_year, company_name, designation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (user_id, enrollment_no, department, degree, pass_year, company_name, designation))
            
            elif role == 'faculty':
                employee_id = request.form.get('employee_id', '').strip()
                department = request.form.get('department', '').strip()
                designation = request.form.get('designation', '').strip()
                qualification = request.form.get('qualification', '').strip()
                
                if not all([employee_id, department, designation, qualification]):
                    flash('Faculty details are incomplete!', 'warning')
                    return redirect(url_for('register', role='faculty'))
                
                c.execute('''INSERT INTO faculty_profile 
                    (user_id, employee_id, department, designation, qualification)
                    VALUES (?, ?, ?, ?, ?)''',
                    (user_id, employee_id, department, designation, qualification))
            
            conn.commit()
            flash(f'{role.capitalize()} Registration Successful! Please Login.', 'success')
            return redirect(url_for('login'))
        
        except sqlite3.IntegrityError as e:
            if conn:
                conn.rollback()
            flash('Email or ID already registered!', 'warning')
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Registration error: {e}")
            flash(f'Registration error: {str(e)}', 'danger')
        finally:
            if conn:
                conn.close()
    
    return render_template('register.html', role=role)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- PROFILE ROUTES ---

@app.route('/profile')
@login_required
def profile():
    if current_user.role == 'student':
        return redirect(url_for('student_profile', user_id=current_user.id))
    elif current_user.role == 'alumni':
        return redirect(url_for('alumni_profile', user_id=current_user.id))
    elif current_user.role == 'faculty':
        return redirect(url_for('faculty_profile', user_id=current_user.id))
    return redirect(url_for('home'))

@app.route('/student/profile/<int:user_id>')
@login_required
def student_profile(user_id):
    if current_user.role not in ['admin', 'student', 'faculty']:
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT * FROM student_profile WHERE user_id = ?', (user_id,)).fetchone()
        
        if not user or not profile:
            flash('Student not found!', 'danger')
            return redirect(url_for('home'))
        
        return render_template('profile_student.html', user=user, profile=profile)
    finally:
        if conn:
            conn.close()

@app.route('/alumni/profile/<int:user_id>')
@login_required
def alumni_profile(user_id):
    if current_user.role not in ['admin', 'alumni', 'student', 'faculty']:
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (user_id,)).fetchone()
        
        if not user or not profile:
            flash('Alumni not found!', 'danger')
            return redirect(url_for('home'))
        
        return render_template('profile_alumni.html', user=user, profile=profile)
    finally:
        if conn:
            conn.close()

@app.route('/faculty/profile/<int:user_id>')
@login_required
def faculty_profile(user_id):
    if current_user.role not in ['admin', 'student', 'alumni', 'faculty']:
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (user_id,)).fetchone()
        
        if not user:
            flash('Faculty not found!', 'danger')
            return redirect(url_for('home'))
        
        # If profile doesn't exist, create a default one
        if not profile:
            try:
                conn.execute('''INSERT INTO faculty_profile 
                    (user_id, employee_id, department, designation, specialization, qualification, experience_years, office_location, office_hours, bio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (user_id, f'FAC{user_id}', 'N/A', 'Faculty', '', '', 0, '', '', ''))
                conn.commit()
                profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (user_id,)).fetchone()
            except Exception as e:
                print(f"Error creating faculty profile: {e}")
                profile = None
        
        return render_template('profile_faculty.html', user=user, profile=profile)
    except Exception as e:
        print(f"Faculty profile error: {e}")
        flash('Error loading profile!', 'danger')
        return redirect(url_for('home'))
    finally:
        if conn:
            conn.close()

@app.route('/admin/users/<role>')
@login_required
def admin_view_users(role):
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        users = conn.execute('SELECT * FROM users WHERE role = ? ORDER BY id DESC', (role,)).fetchall()
        return render_template('admin_view_users.html', users=users, role=role)
    finally:
        if conn:
            conn.close()

# --- DASHBOARDS ---

@app.route('/student/dashboard')
@login_required
def dashboard_student():
    conn = None
    try:
        conn = get_db_connection()
        
        # Fetch alumni with all details
        alumni = conn.execute("""
            SELECT u.id, u.name, u.email, u.phone, 
                   a.enrollment_no, a.department, a.degree, a.pass_year,
                   a.company_name, a.designation, a.work_location, a.experience_years
            FROM users u
            JOIN alumni_profile a ON u.id = a.user_id
            WHERE u.role='alumni'
            ORDER BY a.pass_year DESC
        """).fetchall()
        
        # Fetch faculty members
        faculty = conn.execute("""
            SELECT u.id, u.name, u.email, u.phone,
                   f.department, f.designation, f.office_location
            FROM users u
            JOIN faculty_profile f ON u.id = f.user_id
            WHERE u.role='faculty'
            ORDER BY f.department
        """).fetchall()
        
        # Get current student profile
        student = conn.execute(
            'SELECT * FROM student_profile WHERE user_id = ?',
            (current_user.id,)
        ).fetchone()
        
        return render_template('dashboard_student.html', 
                             alumni=alumni, 
                             faculty=faculty, 
                             student=student)
    finally:
        if conn:
            conn.close()

@app.route('/alumni/dashboard')
@login_required
def dashboard_alumni():
    return render_template('dashboard_alumni.html')

@app.route('/faculty/dashboard')
@login_required
def dashboard_faculty():
    if current_user.role != 'faculty':
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (current_user.id,)).fetchone()
        
        # If profile doesn't exist, create a default one or redirect to complete profile
        if not profile:
            # Try to create a default profile if it doesn't exist
            try:
                conn.execute('''INSERT INTO faculty_profile 
                    (user_id, employee_id, department, designation, specialization, qualification, experience_years, office_location, office_hours, bio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (current_user.id, f'FAC{current_user.id}', 'N/A', 'Faculty', '', '', 0, '', '', ''))
                conn.commit()
                profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (current_user.id,)).fetchone()
            except Exception as e:
                print(f"Error creating default faculty profile: {e}")
                # If still no profile, redirect to edit profile page
                return redirect(url_for('edit_faculty_profile', user_id=current_user.id))
        
        return render_template('dashboard_faculty.html', profile=profile)
    
    except Exception as e:
        print(f"Dashboard faculty error: {e}")
        flash('Error loading dashboard!', 'danger')
        return redirect(url_for('home'))
    finally:
        if conn:
            conn.close()

@app.route('/admin/dashboard')
@login_required
def dashboard_admin():
    if current_user.role != 'admin': 
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        users = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
        a_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='alumni'").fetchone()[0]
        s_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
        f_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='faculty'").fetchone()[0]
        
        chart_data = {
            'years': ['2021', '2022', '2023', '2024', '2025'],
            'placements': [120, 150, 200, 250, 310],
            'funds': [5, 12, 15, 25, 40]
        }
        return render_template('dashboard_admin.html', users=users, a_count=a_count, s_count=s_count, f_count=f_count, chart_data=chart_data)
    finally:
        if conn:
            conn.close()

# --- ALUMNI MEET ROUTES ---

@app.route('/alumni/meet/register', methods=['GET', 'POST'])
@login_required
def alumni_meet_register():
    if current_user.role != 'alumni':
        flash('Only alumni can register for the meet!', 'warning')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        conn = None
        try:
            full_name = request.form.get('full_name', '').strip()
            gender = request.form.get('gender', '')
            dob = request.form.get('dob', '')
            contact_no = request.form.get('contact_no', '').strip()
            email = request.form.get('email', '').strip()
            current_address = request.form.get('current_address', '').strip()
            enrollment_no = request.form.get('enrollment_no', '').strip()
            course = request.form.get('course', '')
            passing_year = request.form.get('passing_year', '')
            current_status = request.form.get('current_status', '')
            company_name = request.form.get('company_name', '')
            designation = request.form.get('designation', '')
            work_location = request.form.get('work_location', '')
            experience_years = request.form.get('experience_years', '')
            university_name = request.form.get('university_name', '')
            higher_study_course = request.form.get('higher_study_course', '')
            higher_study_country = request.form.get('higher_study_country', '')
            higher_study_state = request.form.get('higher_study_state', '')
            enrollment_year = request.form.get('enrollment_year', '')
            contribute_to_college = request.form.get('contribute_to_college', 'No')
            contribution_areas = ','.join(request.form.getlist('contribution_areas'))
            attending_meet = request.form.get('attending_meet', 'No')
            
            if not all([full_name, contact_no, email, enrollment_no, course, passing_year]):
                flash('Please fill in all required fields!', 'warning')
                return render_template('alumni_meet_register.html')
            
            conn = get_db_connection()
            conn.execute('''INSERT INTO alumni_meet_registration 
                (user_id, full_name, gender, dob, contact_no, email, current_address, 
                 enrollment_no, course, passing_year, current_status, company_name, 
                 designation, work_location, experience_years, university_name, 
                 higher_study_course, higher_study_country, higher_study_state, 
                 enrollment_year, contribute_to_college, contribution_areas, attending_meet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (current_user.id, full_name, gender, dob, contact_no, email, current_address,
                 enrollment_no, course, passing_year, current_status, company_name,
                 designation, work_location, experience_years, university_name,
                 higher_study_course, higher_study_country, higher_study_state,
                 enrollment_year, contribute_to_college, contribution_areas, attending_meet))
            conn.commit()
            
            flash('Alumni Meet Registration Successful!', 'success')
            return redirect(url_for('dashboard_alumni'))
        except sqlite3.IntegrityError:
            if conn:
                conn.rollback()
            flash('You have already registered for this meet!', 'warning')
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Alumni meet registration error: {e}")
            flash(f'Error during registration: {str(e)}', 'danger')
        finally:
            if conn:
                conn.close()
    
    return render_template('alumni_meet_register.html')

@app.route('/alumni/meet/view')
@login_required
def alumni_meet_view():
    if current_user.role != 'alumni':
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        registration = conn.execute('SELECT * FROM alumni_meet_registration WHERE user_id = ?', 
                                   (current_user.id,)).fetchone()
        
        if not registration:
            flash('You have not registered for the Alumni Meet yet!', 'info')
            return redirect(url_for('alumni_meet_register'))
        
        return render_template('alumni_meet_view.html', registration=registration)
    finally:
        if conn:
            conn.close()

# --- PROFILE EDIT ROUTES ---

@app.route('/student/profile/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student_profile(user_id):
    if current_user.id != user_id and current_user.role != 'admin':
        flash('You cannot edit this profile!', 'danger')
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            cgpa = request.form.get('cgpa', '')
            skills = request.form.get('skills', '').strip()
            achievements = request.form.get('achievements', '').strip()
            resume_link = request.form.get('resume_link', '').strip()
            semester = request.form.get('semester', '')
            
            # Client-side validation already happens, so only save if data is valid
            # This is a backup validation
            if not name or not phone:
                # Don't redirect - keep form intact by re-rendering
                user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
                profile = conn.execute('SELECT * FROM student_profile WHERE user_id = ?', (user_id,)).fetchone()
                flash('Name and Phone are required!', 'warning')
                return render_template('edit_student_profile.html', user=user, profile=profile)
            
            # Handle profile photo upload
            profile_pic = None
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"student_{user_id}_{datetime.now().timestamp()}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    profile_pic = f"/static/uploads/{filename}"
            
            # Update users table
            if profile_pic:
                conn.execute('UPDATE users SET name = ?, phone = ?, profile_pic = ? WHERE id = ?',
                            (name, phone, profile_pic, user_id))
            else:
                conn.execute('UPDATE users SET name = ?, phone = ? WHERE id = ?',
                            (name, phone, user_id))
            
            # Update student_profile table
            conn.execute('''UPDATE student_profile 
                SET cgpa = ?, skills = ?, achievements = ?, resume_link = ?, semester = ?
                WHERE user_id = ?''',
                (cgpa, skills, achievements, resume_link, semester, user_id))
            
            conn.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('student_profile', user_id=user_id))
        
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT * FROM student_profile WHERE user_id = ?', (user_id,)).fetchone()
        
        if not user or not profile:
            flash('Student not found!', 'danger')
            return redirect(url_for('home'))
        
        return render_template('edit_student_profile.html', user=user, profile=profile)
    
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Edit student profile error: {e}")
        flash(f'Error updating profile: {str(e)}', 'danger')
        return redirect(url_for('student_profile', user_id=user_id))
    finally:
        if conn:
            conn.close()

@app.route('/alumni/profile/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_alumni_profile(user_id):
    if current_user.id != user_id and current_user.role != 'admin':
        flash('You cannot edit this profile!', 'danger')
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            company_name = request.form.get('company_name', '').strip()
            designation = request.form.get('designation', '').strip()
            work_location = request.form.get('work_location', '').strip()
            experience_years = request.form.get('experience_years', '')
            linkedin_url = request.form.get('linkedin_url', '').strip()
            achievements = request.form.get('achievements', '').strip()
            bio = request.form.get('bio', '').strip()
            
            # Client-side validation already happens, so only save if data is valid
            # This is a backup validation
            if not name or not phone:
                # Don't redirect - keep form intact by re-rendering
                user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
                profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (user_id,)).fetchone()
                flash('Name and Phone are required!', 'warning')
                return render_template('edit_alumni_profile.html', user=user, profile=profile)
            
            # Handle profile photo upload
            profile_pic = None
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"alumni_{user_id}_{datetime.now().timestamp()}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    profile_pic = f"/static/uploads/{filename}"
            
            if profile_pic:
                conn.execute('UPDATE users SET name = ?, phone = ?, profile_pic = ? WHERE id = ?',
                            (name, phone, profile_pic, user_id))
            else:
                conn.execute('UPDATE users SET name = ?, phone = ? WHERE id = ?',
                            (name, phone, user_id))
            
            conn.execute('''UPDATE alumni_profile 
                SET company_name = ?, designation = ?, work_location = ?, 
                    experience_years = ?, linkedin_url = ?, achievements = ?, bio = ?
                WHERE user_id = ?''',
                (company_name, designation, work_location, experience_years, 
                 linkedin_url, achievements, bio, user_id))
            
            conn.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('alumni_profile', user_id=user_id))
        
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (user_id,)).fetchone()
        
        if not user or not profile:
            flash('Alumni not found!', 'danger')
            return redirect(url_for('home'))
        
        return render_template('edit_alumni_profile.html', user=user, profile=profile)
    
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Edit alumni profile error: {e}")
        flash(f'Error updating profile: {str(e)}', 'danger')
        return redirect(url_for('alumni_profile', user_id=user_id))
    finally:
        if conn:
            conn.close()

@app.route('/faculty/profile/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_faculty_profile(user_id):
    if current_user.id != user_id and current_user.role != 'admin':
        flash('You cannot edit this profile!', 'danger')
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            specialization = request.form.get('specialization', '').strip()
            experience_years = request.form.get('experience_years', '')
            office_location = request.form.get('office_location', '').strip()
            office_hours = request.form.get('office_hours', '').strip()
            bio = request.form.get('bio', '').strip()
            
            # Client-side validation already happens, so only save if data is valid
            # This is a backup validation
            if not name or not phone:
                # Don't redirect - keep form intact by re-rendering
                user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
                profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (user_id,)).fetchone()
                flash('Name and Phone are required!', 'warning')
                return render_template('edit_faculty_profile.html', user=user, profile=profile)
            
            # Handle profile photo upload
            profile_pic = None
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"faculty_{user_id}_{datetime.now().timestamp()}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    profile_pic = f"/static/uploads/{filename}"
            
            if profile_pic:
                conn.execute('UPDATE users SET name = ?, phone = ?, profile_pic = ? WHERE id = ?',
                            (name, phone, profile_pic, user_id))
            else:
                conn.execute('UPDATE users SET name = ?, phone = ? WHERE id = ?',
                            (name, phone, user_id))
            
            conn.execute('''UPDATE faculty_profile 
                SET specialization = ?, experience_years = ?, office_location = ?, 
                    office_hours = ?, bio = ?
                WHERE user_id = ?''',
                (specialization, experience_years, office_location, office_hours, bio, user_id))
            
            conn.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('faculty_profile', user_id=user_id))
        
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (user_id,)).fetchone()
        
        if not user or not profile:
            flash('Faculty not found!', 'danger')
            return redirect(url_for('home'))
        
        return render_template('edit_faculty_profile.html', user=user, profile=profile)
    
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Edit faculty profile error: {e}")
        flash(f'Error updating profile: {str(e)}', 'danger')
        return redirect(url_for('faculty_profile', user_id=user_id))
    finally:
        if conn:
            conn.close()

# --- PASSWORD CHANGE ROUTES ---

@app.route('/change-password', methods=['GET', 'POST'])
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not all([old_password, new_password, confirm_password]):
            flash('All fields are required!', 'warning')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match!', 'warning')
            return render_template('change_password.html')
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long!', 'warning')
            return render_template('change_password.html')
        
        conn = None
        try:
            conn = get_db_connection()
            user = conn.execute('SELECT password FROM users WHERE id = ?', (current_user.id,)).fetchone()
            
            if not check_password_hash(user['password'], old_password):
                flash('Old password is incorrect!', 'danger')
                return render_template('change_password.html')
            
            new_password_hash = generate_password_hash(new_password)
            conn.execute('UPDATE users SET password = ? WHERE id = ?', 
                        (new_password_hash, current_user.id))
            conn.commit()
            
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))
        
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f'Error changing password: {str(e)}', 'danger')
        finally:
            if conn:
                conn.close()
    
    return render_template('change_password.html')

# Add new routes for comprehensive profile features

# --- PROFILE COMPLETION & ENHANCEMENT ---

@app.route('/profile/complete/<int:user_id>', methods=['GET', 'POST'])
@login_required
def complete_profile(user_id):
    """Complete initial profile setup"""
    if current_user.id != user_id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if request.method == 'POST':
            # Handle profile photo
            profile_pic = None
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{current_user.role}_{user_id}_{datetime.now().timestamp()}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    profile_pic = f"/static/uploads/{filename}"
                    conn.execute('UPDATE users SET profile_pic = ? WHERE id = ?', (profile_pic, user_id))
            
            # Update common fields
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            
            if name and phone:
                conn.execute('UPDATE users SET name = ?, phone = ? WHERE id = ?', (name, phone, user_id))
            
            conn.commit()
            flash('Profile completed successfully!', 'success')
            
            if current_user.role == 'student':
                return redirect(url_for('student_profile', user_id=user_id))
            elif current_user.role == 'alumni':
                return redirect(url_for('alumni_profile', user_id=user_id))
            elif current_user.role == 'faculty':
                return redirect(url_for('faculty_profile', user_id=user_id))
        
        role = user['role']
        return render_template('complete_profile.html', user=user, role=role)
    
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('profile'))
    finally:
        if conn:
            conn.close()

# --- ADMIN FEATURES ---

@app.route('/admin/verify-user/<int:user_id>/<action>')
@login_required
def verify_user(user_id, action):
    """Admin: Verify/Block users"""
    if current_user.role != 'admin':
        flash('Unauthorized!', 'danger')
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        
        if action == 'approve':
            flash('User verified successfully!', 'success')
        elif action == 'block':
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            flash('User blocked/removed!', 'warning')
        
        conn.commit()
        return redirect(url_for('admin_view_users', role='student'))
    
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))
    finally:
        if conn:
            conn.close()

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    """Admin: View analytics and reports"""
    if current_user.role != 'admin':
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        
        # Gather statistics
        stats = {
            'total_users': conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            'students': conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0],
            'alumni': conn.execute("SELECT COUNT(*) FROM users WHERE role='alumni'").fetchone()[0],
            'faculty': conn.execute("SELECT COUNT(*) FROM users WHERE role='faculty'").fetchone()[0],
            'admin': conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0],
            'meet_registrations': conn.execute("SELECT COUNT(*) FROM alumni_meet_registration").fetchone()[0],
        }
        
        return render_template('admin_analytics.html', stats=stats)
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('dashboard_admin'))
    finally:
        if conn:
            conn.close()

# --- NETWORKING & CONNECTIONS ---

@app.route('/network/search', methods=['GET', 'POST'])
@login_required
def search_network():
    """Search and filter users"""
    conn = None
    try:
        conn = get_db_connection()
        results = []
        
        if request.method == 'POST':
            search_term = request.form.get('search', '').strip()
            filter_role = request.form.get('role', '')
            
            if search_term:
                if filter_role:
                    results = conn.execute(
                        "SELECT * FROM users WHERE (name LIKE ? OR email LIKE ?) AND role = ? LIMIT 50",
                        (f"%{search_term}%", f"%{search_term}%", filter_role)
                    ).fetchall()
                else:
                    results = conn.execute(
                        "SELECT * FROM users WHERE name LIKE ? OR email LIKE ? LIMIT 50",
                        (f"%{search_term}%", f"%{search_term}%")
                    ).fetchall()
        
        return render_template('search_network.html', results=results)
    
    finally:
        if conn:
            conn.close()

# --- NOTIFICATIONS & UPDATES ---

@app.route('/notifications')
@login_required
def notifications():
    """View user notifications"""
    # Placeholder for notifications system
    return render_template('notifications.html')

# Import the social routes blueprint
try:
    from routes.social_routes import social_bp
    app.register_blueprint(social_bp)
except ImportError:
    print("Warning: social_routes blueprint not found")

# --- STUDENT TO ALUMNI UPGRADE ---

@app.route('/student/upgrade-to-alumni', methods=['GET', 'POST'])
@login_required
def upgrade_to_alumni():
    """Upgrade student role to alumni"""
    if current_user.role != 'student':
        flash('Only students can upgrade to alumni!', 'warning')
        return redirect(url_for('home'))
    
    conn = None
    try:
        conn = get_db_connection()
        
        if request.method == 'POST':
            # Get student profile
            student_profile = conn.execute(
                'SELECT * FROM student_profile WHERE user_id = ?', 
                (current_user.id,)
            ).fetchone()
            
            if not student_profile:
                flash('Student profile not found!', 'danger')
                return redirect(url_for('dashboard_student'))
            
            # Get form data
            pass_year = request.form.get('pass_year', '')
            company_name = request.form.get('company_name', '')
            designation = request.form.get('designation', '')
            
            if not pass_year:
                flash('Year of passing is required!', 'warning')
                return render_template('upgrade_to_alumni.html', profile=student_profile)
            
            # Update user role
            conn.execute('UPDATE users SET role = ? WHERE id = ?', ('alumni', current_user.id))
            
            # Create alumni profile
            conn.execute('''INSERT INTO alumni_profile 
                (user_id, enrollment_no, department, degree, pass_year, company_name, designation)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (current_user.id, student_profile['enrollment_no'], 
                 student_profile['department'], student_profile['degree'],
                 pass_year, company_name, designation))
            
            conn.commit()
            
            flash('Successfully upgraded to Alumni! Your role has been changed.', 'success')
            return redirect(url_for('alumni_profile', user_id=current_user.id))
        
        # GET request - fetch student profile
        student_profile = conn.execute(
            'SELECT * FROM student_profile WHERE user_id = ?', 
            (current_user.id,)
        ).fetchone()
        
        if not student_profile:
            flash('Student profile not found!', 'danger')
            return redirect(url_for('dashboard_student'))
        
        return render_template('upgrade_to_alumni.html', profile=student_profile)
    
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Upgrade to alumni error: {e}")
        flash(f'Error upgrading to alumni: {str(e)}', 'danger')
        return redirect(url_for('dashboard_student'))
    finally:
        if conn:
            conn.close()

# --- API ROUTES FOR MODALS ---

@app.route('/api/faculty/students')
@login_required
def get_faculty_students():
    """Get all students for faculty dashboard"""
    if current_user.role != 'faculty':
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = None
    try:
        conn = get_db_connection()
        
        # Get all students
        students = conn.execute('''
            SELECT u.id, u.name, u.email, u.phone, u.profile_pic, 
                   sp.enrollment_no, sp.department, sp.degree, sp.semester, sp.cgpa, sp.skills
            FROM users u
            LEFT JOIN student_profile sp ON u.id = sp.user_id
            WHERE u.role = 'student'
            ORDER BY u.name ASC
        ''').fetchall()
        
        total = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = ?', ('student',)).fetchone()['count']
        
        return jsonify({
            'students': [dict(s) for s in students],
            'total_students': total
        })
    except Exception as e:
        print(f"Error getting students: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/faculty/alumni')
@login_required
def get_faculty_alumni():
    """Get all alumni for faculty dashboard"""
    if current_user.role != 'faculty':
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = None
    try:
        conn = get_db_connection()
        
        # Get all alumni
        alumni = conn.execute('''
            SELECT u.id, u.name, u.email, u.phone, u.profile_pic,
                   ap.department, ap.company_name, ap.designation, ap.work_location, ap.experience_years, ap.bio
            FROM users u
            LEFT JOIN alumni_profile ap ON u.id = ap.user_id
            WHERE u.role = 'alumni'
            ORDER BY u.name ASC
        ''').fetchall()
        
        total = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = ?', ('alumni',)).fetchone()['count']
        
        return jsonify({
            'alumni': [dict(a) for a in alumni],
            'total_alumni': total
        })
    except Exception as e:
        print(f"Error getting alumni: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/alumni/<int:user_id>')
@login_required
def get_alumni_details(user_id):
    """Get alumni details for modal display"""
    if current_user.role not in ['admin', 'alumni', 'student', 'faculty']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (user_id,)).fetchone()
        
        if not user or not profile:
            return jsonify({'error': 'Alumni not found'}), 404
        
        return jsonify({
            'user': dict(user),
            'profile': dict(profile)
        })
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=app.config['DEBUG'])