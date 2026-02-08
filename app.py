

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
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
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv(
    'MAIL_DEFAULT_SENDER',
    app.config['MAIL_USERNAME']
)

mail = Mail(app)
# ===== EMAIL CONFIGURATION =====
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', True)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'rajendramohan7800@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your_app_password_here')
app.config['MAIL_DEFAULT_SENDER'] = 'noreply@alumnihub.com'


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

def log_registration(conn, user_id, name, email, phone, role, enrollment_no=None,
                    employee_id=None, department=None, degree=None, pass_year=None,
                    company_name=None, designation=None, experience_years=None):
    """
    Log user registration to tracking table with role-specific details
    """
    try:
        c = conn.cursor()
        c.execute('''INSERT INTO registration_log
            (user_id, name, email, phone, role, enrollment_no, employee_id, department,
             degree, pass_year, company_name, designation, experience_years)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, name, email, phone, role, enrollment_no, employee_id, department,
             degree, pass_year, company_name, designation, experience_years))
        conn.commit()
        print(f"✓ Registration logged for {role}: {name} ({email})")
    except Exception as e:
        print(f"Error logging registration: {e}")

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

        # Unified Connection Requests Table (Role-Agnostic)
        # Works for Student->Alumni, Student->Faculty, Alumni->Faculty, etc.
        c.execute('''
            CREATE TABLE IF NOT EXISTS connection_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id),
                UNIQUE(sender_id, receiver_id)
            )
        ''')

        # Unified Connections/Friends Table
        # Stores accepted friendships between any two users
        c.execute('''
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id_1 INTEGER NOT NULL,
                user_id_2 INTEGER NOT NULL,
                connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id_1) REFERENCES users(id),
                FOREIGN KEY (user_id_2) REFERENCES users(id),
                UNIQUE(user_id_1, user_id_2)
            )
        ''')

        # Registration Tracking Table - Logs all user registrations
        c.execute('''
            CREATE TABLE IF NOT EXISTS registration_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                role TEXT NOT NULL,
                enrollment_no TEXT,
                employee_id TEXT,
                department TEXT,
                degree TEXT,
                pass_year INTEGER,
                company_name TEXT,
                designation TEXT,
                experience_years INTEGER,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

            # ===== SEND EMAIL TO ADMIN =====
            try:
                admin_email = os.getenv('ADMIN_EMAIL', 'rajendramohan7800@gmail.com')
                submission_time = datetime.now().strftime('%d %B %Y at %I:%M %p')

                # Email to admin
                msg = Message(
                    subject=f'📬 New Contact: {subject} | Alumni Hub',
                    recipients=[admin_email],
                    html=f'''
                    <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #f0f4ff 0%, #f8f9ff 100%); padding: 30px; border-radius: 15px;">
                        <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; border-top: 5px solid #1e3a8a; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                            <h1 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.8rem;">📧 New Contact Message Received</h1>

                            <div style="background: linear-gradient(135deg, rgba(30, 58, 138, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #0ea5e9;">
                                <p style="margin: 0 0 8px 0; color: #0ea5e9; font-weight: 700; font-size: 0.9rem;">📌 PROJECT SOURCE</p>
                                <p style="margin: 0; color: #1e3a8a; font-size: 1.2rem; font-weight: 800;">🎓 ALUMNI HUB MANAGEMENT SYSTEM</p>
                                <p style="margin: 5px 0 0 0; color: #666; font-size: 0.85rem;">Contact Form Submission</p>
                            </div>
                        </div>

                        <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
                            <h3 style="color: #1e3a8a; margin: 0 0 15px 0; border-bottom: 2px solid #f59e0b; padding-bottom: 10px; font-size: 1.1rem;">👤 Sender Information</h3>

                            <table style="width: 100%; border-collapse: collapse;">
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a; width: 30%;">Name:</td>
                                    <td style="padding: 12px 0; color: #333;">{name}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Email:</td>
                                    <td style="padding: 12px 0; color: #333;"><a href="mailto:{email}" style="color: #0ea5e9; text-decoration: none; font-weight: 600;">{email}</a></td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Subject:</td>
                                    <td style="padding: 12px 0; color: #333; font-weight: 600;">{subject}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Submitted:</td>
                                    <td style="padding: 12px 0; color: #666; font-size: 0.9rem;">{submission_time}</td>
                                </tr>
                            </table>
                        </div>

                        <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #f59e0b; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
                            <h3 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.1rem;">💬 Message Content</h3>
                            <p style="margin: 0; color: #333; line-height: 1.8; white-space: pre-wrap; word-wrap: break-word;">{message}</p>
                        </div>

                        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #0ea5e9 100%); padding: 20px; border-radius: 12px; margin-bottom: 15px; color: white; text-align: center;">
                            <p style="margin: 0; font-size: 0.95rem; font-weight: 600;">Quick Reply</p>
                            <p style="margin: 10px 0 0 0; font-size: 0.85rem; opacity: 0.9;">Reply directly to this email or contact {name} at {email}</p>
                        </div>

                        <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                            <p style="margin: 0; color: #666; font-size: 0.85rem;">
                                <strong style="color: #1e3a8a;">Alumni Hub</strong> • Contact Management System<br>
                                This message was sent from the Alumni Hub contact form.
                            </p>
                        </div>
                    </div>
                    ''',
                    reply_to=email
                )

                mail.send(msg)

                # Email to user (confirmation)
                user_msg = Message(
                    subject='✓ Message Received - Alumni Hub',
                    recipients=[email],
                    html=f'''
                    <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #f0f4ff 0%, #f8f9ff 100%); padding: 30px; border-radius: 15px;">
                        <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; border-top: 5px solid #10b981; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                            <h1 style="color: #10b981; margin: 0 0 15px 0; font-size: 1.8rem;">✓ Message Received Successfully!</h1>

                            <div style="background: linear-gradient(135deg, rgba(30, 58, 138, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #0ea5e9;">
                                <p style="margin: 0 0 8px 0; color: #0ea5e9; font-weight: 700; font-size: 0.9rem;">📌 PROJECT</p>
                                <p style="margin: 0; color: #1e3a8a; font-size: 1.2rem; font-weight: 800;">🎓 ALUMNI HUB MANAGEMENT SYSTEM</p>
                                <p style="margin: 5px 0 0 0; color: #666; font-size: 0.85rem;">Your contact message has been submitted</p>
                            </div>
                        </div>

                        <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
                            <p style="color: #333; line-height: 1.8; margin: 0 0 15px 0;">Dear <strong>{name}</strong>,</p>

                            <p style="color: #333; line-height: 1.8; margin: 0;">
                                Thank you for reaching out to us through the Alumni Hub contact form! We have successfully received your message and appreciate you taking the time to get in touch with us.
                            </p>
                        </div>

                        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(10, 150, 105, 0.08) 100%); padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #10b981; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
                            <h3 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.1rem;">📋 Your Submission Details</h3>

                            <table style="width: 100%; border-collapse: collapse;">
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 10px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a; width: 35%;">Subject:</td>
                                    <td style="padding: 10px 0; color: #333;">{subject}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 10px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Submitted On:</td>
                                    <td style="padding: 10px 0; color: #666; font-size: 0.95rem;">{submission_time}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Source:</td>
                                    <td style="padding: 10px 0; color: #333; font-weight: 600;">🎓 Alumni Hub Contact Form</td>
                                </tr>
                            </table>
                        </div>

                        <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
                            <h3 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.1rem;">⏱️ What's Next?</h3>
                            <ul style="margin: 0; padding-left: 20px; color: #333; line-height: 1.8;">
                                <li style="margin-bottom: 8px;">Our team will review your message</li>
                                <li style="margin-bottom: 8px;">We'll respond within 24-48 business hours</li>
                                <li style="margin-bottom: 8px;">Check your email for our reply</li>
                                <li>If urgent, you can reach us directly</li>
                            </ul>
                        </div>

                        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #0ea5e9 100%); padding: 20px; border-radius: 12px; margin-bottom: 15px; color: white; text-align: center;">
                            <p style="margin: 0; font-size: 0.95rem; font-weight: 600;">Contact Information</p>
                            <p style="margin: 10px 0 0 0; font-size: 0.9rem; opacity: 0.95;">
                                📧 support@alumnihub.com | 📞 +91-9876-543-210
                            </p>
                        </div>

                        <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                            <p style="color: #333; margin: 0; line-height: 1.6; font-size: 0.95rem;">
                                <strong style="color: #1e3a8a;">Alumni Hub</strong><br>
                                <span style="color: #666; font-size: 0.9rem;">Building Connections, Creating Opportunities</span>
                            </p>
                            <p style="margin: 10px 0 0 0; color: #999; font-size: 0.85rem;">
                                © 2026 Alumni Hub. All rights reserved.
                            </p>
                        </div>
                    </div>
                    '''
                )

                mail.send(user_msg)

            except Exception as email_error:
                print(f"Email sending error: {email_error}")
                # Continue even if email fails

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

                # Log registration with student details
                log_registration(conn, user_id, name, email, phone, role,
                               enrollment_no=enrollment_no, department=department, degree=degree)

            elif role == 'alumni':
                enrollment_no = request.form.get('enrollment_no', '').strip()
                department = request.form.get('department', '').strip()
                degree = request.form.get('degree', '').strip()
                pass_year = request.form.get('pass_year', '')
                company_name = request.form.get('company_name', '')
                designation = request.form.get('designation', '')
                experience_years = request.form.get('experience_years', '')

                if not all([enrollment_no, department, degree, pass_year]):
                    flash('Alumni details are incomplete!', 'warning')
                    return redirect(url_for('register', role='alumni'))

                c.execute('''INSERT INTO alumni_profile
                    (user_id, enrollment_no, department, degree, pass_year, company_name, designation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (user_id, enrollment_no, department, degree, pass_year, company_name, designation))

                # Log registration with alumni details
                log_registration(conn, user_id, name, email, phone, role,
                               enrollment_no=enrollment_no, department=department, degree=degree,
                               pass_year=int(pass_year) if pass_year else None,
                               company_name=company_name, designation=designation,
                               experience_years=int(experience_years) if experience_years else None)

            elif role == 'faculty':
                employee_id = request.form.get('employee_id', '').strip()
                department = request.form.get('department', '').strip()
                designation = request.form.get('designation', '').strip()
                qualification = request.form.get('qualification', '').strip()
                experience_years = request.form.get('experience_years', '')

                if not all([employee_id, department, designation, qualification]):
                    flash('Faculty details are incomplete!', 'warning')
                    return redirect(url_for('register', role='faculty'))

                c.execute('''INSERT INTO faculty_profile
                    (user_id, employee_id, department, designation, qualification)
                    VALUES (?, ?, ?, ?, ?)''',
                    (user_id, employee_id, department, designation, qualification))

                # Log registration with faculty details
                log_registration(conn, user_id, name, email, phone, role,
                               employee_id=employee_id, department=department,
                               designation=designation, experience_years=int(experience_years) if experience_years else None)

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
    elif current_user.role == 'admin':
        return redirect(url_for('admin_profile', user_id=current_user.id))
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

@app.route('/admin/profile/<int:user_id>')
@login_required
def admin_profile(user_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

        if not user or user['role'] != 'admin':
            flash('Admin not found!', 'danger')
            return redirect(url_for('home'))

        return render_template('profile_admin.html', user=user)
    except Exception as e:
        print(f"Admin profile error: {e}")
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

        # Get pending connection requests
        pending_requests = conn.execute("""
            SELECT cr.id, cr.sender_id, cr.receiver_id, cr.status, cr.created_at,
                   u.name, u.email, u.role, u.profile_pic
            FROM connection_requests cr
            JOIN users u ON cr.sender_id = u.id
            WHERE cr.receiver_id = ? AND cr.status = 'pending'
            ORDER BY cr.created_at DESC
        """, (current_user.id,)).fetchall()

        # Fetch other students for the directory
        other_students = conn.execute("""
            SELECT u.id, u.name, u.email, u.phone, u.profile_pic,
                   s.department, s.degree, s.semester
            FROM users u
            JOIN student_profile s ON u.id = s.user_id
            WHERE u.role='student' AND u.id != ?
            ORDER BY u.name ASC
        """, (current_user.id,)).fetchall()

        return render_template('dashboard_student.html',
                             alumni=alumni,
                             faculty=faculty,
                             student=student,
                             other_students=other_students,
                             pending_requests=pending_requests,
                             pending_count=len(pending_requests))
    finally:
        if conn:
            conn.close()

@app.route('/alumni/dashboard')
@login_required
def dashboard_alumni():
    conn = None
    try:
        conn = get_db_connection()

        # Get pending connection requests
        pending_requests = conn.execute("""
            SELECT cr.id, cr.sender_id, cr.receiver_id, cr.status, cr.created_at,
                   u.name, u.email, u.role, u.profile_pic
            FROM connection_requests cr
            JOIN users u ON cr.sender_id = u.id
            WHERE cr.receiver_id = ? AND cr.status = 'pending'
            ORDER BY cr.created_at DESC
        """, (current_user.id,)).fetchall()

        # Get alumni profile for completeness tracking
        alumni_profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (current_user.id,)).fetchone()

        return render_template('dashboard_alumni.html',
                             pending_requests=pending_requests,
                             pending_count=len(pending_requests),
                             alumni=alumni_profile)
    finally:
        if conn:
            conn.close()

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

        # Get pending connection requests
        pending_requests = conn.execute("""
            SELECT cr.id, cr.sender_id, cr.receiver_id, cr.status, cr.created_at,
                   u.name, u.email, u.role, u.profile_pic
            FROM connection_requests cr
            JOIN users u ON cr.sender_id = u.id
            WHERE cr.receiver_id = ? AND cr.status = 'pending'
            ORDER BY cr.created_at DESC
        """, (current_user.id,)).fetchall()

        # Fetch alumni for directory
        alumni = conn.execute("""
            SELECT u.id, u.name, u.email, u.phone, u.profile_pic,
                   a.enrollment_no, a.department, a.degree, a.pass_year,
                   a.company_name, a.designation, a.work_location, a.experience_years
            FROM users u
            JOIN alumni_profile a ON u.id = a.user_id
            WHERE u.role='alumni'
            ORDER BY a.pass_year DESC
        """).fetchall()

        # Fetch all students for directory
        students = conn.execute("""
            SELECT u.id, u.name, u.email, u.phone, u.profile_pic,
                   s.department, s.degree, s.semester, s.skills, s.cgpa
            FROM users u
            JOIN student_profile s ON u.id = s.user_id
            WHERE u.role='student'
            ORDER BY u.name ASC
        """).fetchall()

        # Fetch other faculty members (colleagues)
        faculty_members = conn.execute("""
            SELECT u.id, u.name, u.email, u.phone, u.profile_pic,
                   f.department, f.designation, f.office_location, f.specialization
            FROM users u
            JOIN faculty_profile f ON u.id = f.user_id
            WHERE u.role='faculty' AND u.id != ?
            ORDER BY f.department
        """, (current_user.id,)).fetchall()

        return render_template('dashboard_faculty.html',
                             profile=profile,
                             pending_requests=pending_requests,
                             pending_count=len(pending_requests),
                             alumni=alumni,
                             students=students,
                             faculty=faculty_members)

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
        
        # Dynamic Chart Data Calculation
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - 4, current_year + 1)]
        
        placements_data = []
        events_data = []
        
        for year in years:
            # Get placement counts for this year
            p_count = conn.execute("""
                SELECT COUNT(*) FROM alumni_profile 
                WHERE pass_year = ? AND company_name IS NOT NULL AND company_name != ''
            """, (int(year),)).fetchone()[0]
            placements_data.append(p_count)
            
            # Get event registrations for this year
            e_count = conn.execute("""
                SELECT COUNT(*) FROM alumni_meet_registration 
                WHERE strftime('%Y', created_at) = ?
            """, (year,)).fetchone()[0]
            events_data.append(e_count)

        chart_data = {
            'years': years,
            'placements': placements_data,
            'events': events_data
        }
        
        # Total event registrations for stat card
        event_total = sum(events_data)
        
        return render_template('dashboard_admin.html', 
                               users=users, 
                               a_count=a_count, 
                               s_count=s_count, 
                               f_count=f_count, 
                               event_total=event_total,
                               chart_data=chart_data)
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
        if not user:
            flash('User not found!', 'danger')
            return redirect(url_for('home'))

        profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (user_id,)).fetchone()

        # If profile doesn't exist, create it
        if not profile:
            try:
                conn.execute('''INSERT INTO alumni_profile
                    (user_id, enrollment_no, department, degree, pass_year, company_name, designation,
                     work_location, experience_years, linkedin_url, achievements, bio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (user_id, '', '', '', '', '', '', '', '', '', '', ''))
                conn.commit()
                profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (user_id,)).fetchone()
            except Exception as e:
                print(f"Error creating alumni profile: {e}")
                flash('Error loading profile!', 'danger')
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

@app.route('/admin/profile/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_admin_profile(user_id):
    if current_user.id != user_id and current_user.role != 'admin':
        flash('You cannot edit this profile!', 'danger')
        return redirect(url_for('home'))

    if current_user.role != 'admin':
        flash('Only admins can edit admin profiles!', 'danger')
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()

            # Validation
            if not name or not email or not phone:
                user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
                flash('Name, Email, and Phone are required!', 'warning')
                return render_template('edit_admin_profile.html', user=user)

            # Handle profile photo upload
            profile_pic = None
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"admin_{user_id}_{datetime.now().timestamp()}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    profile_pic = f"/static/uploads/{filename}"

            # Update users table
            if profile_pic:
                conn.execute('UPDATE users SET name = ?, email = ?, phone = ?, profile_pic = ? WHERE id = ?',
                            (name, email, phone, profile_pic, user_id))
            else:
                conn.execute('UPDATE users SET name = ?, email = ?, phone = ? WHERE id = ?',
                            (name, email, phone, user_id))

            conn.commit()
            flash('Admin profile updated successfully!', 'success')
            return redirect(url_for('admin_profile', user_id=user_id))

        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

        if not user or user['role'] != 'admin':
            flash('Admin not found!', 'danger')
            return redirect(url_for('home'))

        return render_template('edit_admin_profile.html', user=user)

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Edit admin profile error: {e}")
        flash(f'Error updating profile: {str(e)}', 'danger')
        return redirect(url_for('admin_profile', user_id=user_id))
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

@app.route('/admin/registrations')
@login_required
def admin_registrations():
    """Admin: View registration logs"""
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get filter and search parameters
        role_filter = request.args.get('role_filter', '')
        search_query = request.args.get('search', '')

        # Build query with filters
        query = 'SELECT * FROM registration_log WHERE 1=1'
        params = []

        if role_filter:
            query += ' AND role = ?'
            params.append(role_filter)

        if search_query:
            query += ' AND (name LIKE ? OR email LIKE ?)'
            search_term = f'%{search_query}%'
            params.extend([search_term, search_term])

        query += ' ORDER BY registered_at DESC'

        registrations = c.execute(query, params).fetchall()

        # Get statistics
        stats = {
            'students': c.execute("SELECT COUNT(*) FROM registration_log WHERE role='student'").fetchone()[0],
            'alumni': c.execute("SELECT COUNT(*) FROM registration_log WHERE role='alumni'").fetchone()[0],
            'faculty': c.execute("SELECT COUNT(*) FROM registration_log WHERE role='faculty'").fetchone()[0],
            'total': c.execute("SELECT COUNT(*) FROM registration_log").fetchone()[0],
        }

        return render_template('admin_registrations.html',
                             registrations=registrations,
                             stats=stats,
                             current_filter=role_filter,
                             search_query=search_query)

    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('dashboard_admin'))
    finally:
        if conn:
            conn.close()

@app.route('/api/download-csv/<role>')
@login_required
def download_csv(role):
    """Download user data as CSV by role"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    import csv
    from io import StringIO
    from flask import make_response

    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Prepare CSV
        output = StringIO()
        writer = csv.writer(output)

        if role.lower() == 'student':
            # Student data with profiles
            c.execute('''
                SELECT u.id, u.name, u.email, u.phone, u.role,
                       s.enrollment_no, s.semester, s.cgpa, s.skills, s.department
                FROM users u
                LEFT JOIN student_profile s ON u.id = s.user_id
                WHERE u.role = 'student'
                ORDER BY u.id DESC
            ''')

            writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Role',
                           'Enrollment No', 'Semester', 'CGPA', 'Skills', 'Department'])

            for row in c.fetchall():
                writer.writerow([
                    row['id'], row['name'], row['email'], row['phone'],
                    row['role'], row['enrollment_no'] or '', row['semester'] or '',
                    row['cgpa'] or '', row['skills'] or '', row['department'] or ''
                ])

        elif role.lower() == 'alumni':
            # Alumni data with profiles
            c.execute('''
                SELECT u.id, u.name, u.email, u.phone, u.role,
                       a.enrollment_no, a.degree, a.pass_year, a.company_name,
                       a.designation, a.experience_years, a.department
                FROM users u
                LEFT JOIN alumni_profile a ON u.id = a.user_id
                WHERE u.role = 'alumni'
                ORDER BY u.id DESC
            ''')

            writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Role',
                           'Enrollment No', 'Degree', 'Pass Year', 'Company',
                           'Designation', 'Experience (Years)', 'Department'])

            for row in c.fetchall():
                writer.writerow([
                    row['id'], row['name'], row['email'], row['phone'],
                    row['role'], row['enrollment_no'] or '', row['degree'] or '',
                    row['pass_year'] or '', row['company_name'] or '',
                    row['designation'] or '', row['experience_years'] or '',
                    row['department'] or ''
                ])

        elif role.lower() == 'faculty':
            # Faculty data with profiles
            c.execute('''
                SELECT u.id, u.name, u.email, u.phone, u.role,
                       f.employee_id, f.designation, f.specialization, f.experience_years,
                       f.office_hours, f.department
                FROM users u
                LEFT JOIN faculty_profile f ON u.id = f.user_id
                WHERE u.role = 'faculty'
                ORDER BY u.id DESC
            ''')

            writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Role',
                           'Employee ID', 'Designation', 'Specialization',
                           'Experience (Years)', 'Office Hours', 'Department'])

            for row in c.fetchall():
                writer.writerow([
                    row['id'], row['name'], row['email'], row['phone'],
                    row['role'], row['employee_id'] or '', row['designation'] or '',
                    row['specialization'] or '', row['experience_years'] or '',
                    row['office_hours'] or '', row['department'] or ''
                ])

        elif role.lower() == 'all':
            # All users combined
            c.execute('''
                SELECT u.id, u.name, u.email, u.phone, u.role
                FROM users u
                ORDER BY u.id DESC
            ''')

            writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Role'])

            for row in c.fetchall():
                writer.writerow([
                    row['id'], row['name'], row['email'],
                    row['phone'], row['role']
                ])

        else:
            return jsonify({'error': 'Invalid role'}), 400

        conn.close()

        # Get CSV content
        csv_data = output.getvalue()

        # Create response with proper headers
        response = make_response(csv_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{role.upper()}_Users_{timestamp}.csv'

        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Length'] = len(csv_data)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response, 200

    except Exception as e:
        print(f"Error generating CSV: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# --- DATABASE DOWNLOAD ROUTES ---

@app.route('/api/download-db/<db_type>')
@login_required
def download_database(db_type):
    """Download database files for student, alumni, faculty or complete database"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    import shutil
    import tempfile
    from flask import send_file

    try:
        db_types = {
            'college_pro': 'Complete College Database (All Users)',
            'student': 'Student Database Only',
            'alumni': 'Alumni Database Only',
            'faculty': 'Faculty Database Only'
        }

        if db_type not in db_types:
            return jsonify({'error': 'Invalid database type'}), 400

        # For now, we'll send the complete database file
        # In the future, you can create filtered databases
        db_file = DB_NAME  # alumni_hub.db

        if not os.path.exists(db_file):
            return jsonify({'error': 'Database file not found'}), 404

        # Create a temporary copy
        temp_fd, temp_path = tempfile.mkstemp(suffix='.db')
        os.close(temp_fd)

        try:
            shutil.copy2(db_file, temp_path)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{db_type.upper()}_Database_{timestamp}.db'

            return send_file(
                temp_path,
                mimetype='application/x-sqlite3',
                as_attachment=True,
                download_name=filename
            )
        except Exception as copy_error:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise copy_error

    except Exception as e:
        print(f"Error downloading database: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# --- USER DELETION ROUTES ---

@app.route('/api/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user and all their data from the database"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized: Only admins can delete users'}), 403

    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get user details first for logging
        user = c.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        # PROTECTION: Prevent deletion of super admin account
        if user['email'] == 'admin@college.edu':
            conn.close()
            return jsonify({'error': 'Cannot delete the Super Admin account. This account is protected.'}), 403

        user_role = user['role']
        user_name = user['name']
        user_email = user['email']

        print(f"[DELETE DEBUG] Starting deletion for User ID: {user_id}, Role: {user_role}")

        # Delete from profile tables first (cascading)
        if user_role == 'student':
            result = c.execute('DELETE FROM student_profile WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] student_profile rows deleted: {result.rowcount}")
        elif user_role == 'alumni':
            result = c.execute('DELETE FROM alumni_profile WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] alumni_profile rows deleted: {result.rowcount}")
        elif user_role == 'faculty':
            result = c.execute('DELETE FROM faculty_profile WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] faculty_profile rows deleted: {result.rowcount}")

        # Delete from alumni_meet_registration (can be deleted for any user)
        result_amr = c.execute('DELETE FROM alumni_meet_registration WHERE user_id = ?', (user_id,))
        print(f"[DELETE DEBUG] alumni_meet_registration rows deleted: {result_amr.rowcount}")

        # Delete from registration_log (can be deleted for any user)
        try:
            result_reglog = c.execute('DELETE FROM registration_log WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] registration_log rows deleted: {result_reglog.rowcount}")
        except Exception as e:
            print(f"[DELETE DEBUG] registration_log table error: {e}")

        # Delete from connection tables
        result1 = c.execute('DELETE FROM connection_requests WHERE sender_id = ? OR receiver_id = ?', (user_id, user_id))
        print(f"[DELETE DEBUG] connection_requests rows deleted: {result1.rowcount}")

        result2 = c.execute('DELETE FROM connections WHERE user_id_1 = ? OR user_id_2 = ?', (user_id, user_id))
        print(f"[DELETE DEBUG] connections rows deleted: {result2.rowcount}")

        # Delete from other related tables (if they exist)
        try:
            result3 = c.execute('DELETE FROM posts WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] posts rows deleted: {result3.rowcount}")
        except Exception as e:
            print(f"[DELETE DEBUG] posts table error (may not exist): {e}")

        try:
            result4 = c.execute('DELETE FROM comments WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] comments rows deleted: {result4.rowcount}")
        except Exception as e:
            print(f"[DELETE DEBUG] comments table error (may not exist): {e}")

        try:
            result5 = c.execute('DELETE FROM likes WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] likes rows deleted: {result5.rowcount}")
        except Exception as e:
            print(f"[DELETE DEBUG] likes table error (may not exist): {e}")

        # Finally, delete the user record
        result6 = c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        print(f"[DELETE DEBUG] users rows deleted: {result6.rowcount}")

        conn.commit()
        conn.close()

        # Log the deletion
        print(f"[ADMIN DELETE] ✅ Successfully deleted User ID: {user_id}, Name: {user_name}, Email: {user_email}, Role: {user_role}")

        return jsonify({
            'success': True,
            'message': f'User "{user_name}" ({user_email}) has been permanently deleted from the database',
            'user_id': user_id,
            'user_name': user_name
        }), 200

    except Exception as e:
        print(f"[ADMIN DELETE] ❌ Error deleting user: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error deleting user: {str(e)}'}), 500

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

# Import the connection routes blueprint
try:
    from routes.connection_routes import connection_bp
    app.register_blueprint(connection_bp)
except ImportError:
    print("Warning: connection_routes blueprint not found")

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
        user = conn.execute('SELECT id, name, email, profile_pic FROM users WHERE id = ?', (user_id,)).fetchone()
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

@app.route('/api/student/<int:user_id>')
@login_required
def get_student_details(user_id):
    """Get student details for modal display"""
    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT id, name, email, profile_pic FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT department, degree, semester FROM student_profile WHERE user_id = ?', (user_id,)).fetchone()

        if not user or not profile:
            return jsonify({'error': 'Student not found'}), 404

        return jsonify({
            'user': dict(user),
            'profile': dict(profile)
        })
    finally:
        if conn:
            conn.close()

# ===== UNIFIED CONNECTION REQUEST SYSTEM (Role-Agnostic) =====

@app.route('/api/connection-request/send', methods=['POST'])
@login_required
def send_connection_request():
    """
    Send a connection request from current user to any other user.
    Works for Student->Alumni, Student->Faculty, Alumni->Student, etc.
    """
    try:
        data = request.get_json()
        receiver_id = data.get('receiver_id')

        # Validation
        if not receiver_id or receiver_id == current_user.id:
            return jsonify({'error': 'Invalid recipient'}), 400

        conn = get_db_connection()
        c = conn.cursor()

        # Check if receiver exists
        receiver = c.execute('SELECT * FROM users WHERE id = ?', (receiver_id,)).fetchone()
        if not receiver:
            conn.close()
            return jsonify({'error': 'Recipient not found'}), 404

        # Check if already connected
        existing_connection = c.execute('''
            SELECT * FROM connections
            WHERE (user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)
        ''', (current_user.id, receiver_id, receiver_id, current_user.id)).fetchone()

        if existing_connection:
            conn.close()
            return jsonify({'error': 'Already connected', 'status': 'connected'}), 400

        # Check if request already pending
        existing_request = c.execute('''
            SELECT * FROM connection_requests
            WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
        ''', (current_user.id, receiver_id)).fetchone()

        if existing_request:
            conn.close()
            return jsonify({'error': 'Request already sent', 'status': 'pending'}), 400

        # Check for mutual request (auto-connect)
        mutual_request = c.execute('''
            SELECT * FROM connection_requests
            WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
        ''', (receiver_id, current_user.id)).fetchone()

        if mutual_request:
            # Auto-accept mutual request
            c.execute('UPDATE connection_requests SET status = ? WHERE sender_id = ? AND receiver_id = ?',
                     ('accepted', receiver_id, current_user.id))
            c.execute('INSERT INTO connections (user_id_1, user_id_2) VALUES (?, ?)',
                     (min(current_user.id, receiver_id), max(current_user.id, receiver_id)))
            conn.commit()

            # Send email to receiver about mutual connection
            try:
                send_connection_email(
                    receiver['email'],
                    receiver['name'],
                    current_user.name,
                    current_user.role,
                    'mutual'
                )
            except Exception as e:
                print(f"Email error: {e}")

            conn.close()
            return jsonify({'success': True, 'status': 'connected', 'message': 'Now connected!'}), 200

        # Create new request
        c.execute('''
            INSERT INTO connection_requests (sender_id, receiver_id, status)
            VALUES (?, ?, 'pending')
        ''', (current_user.id, receiver_id))

        conn.commit()

        # Send email notification to receiver
        try:
            send_connection_email(
                receiver['email'],
                receiver['name'],
                current_user.name,
                current_user.role,
                'request'
            )
        except Exception as e:
            print(f"Email error: {e}")

        conn.close()

        return jsonify({'success': True, 'status': 'pending', 'message': 'Request sent'}), 200

    except Exception as e:
        print(f"Error sending connection request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/connection-request/accept/<int:sender_id>', methods=['POST'])
@login_required
def accept_connection_request(sender_id):
    """Accept a connection request"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get sender details for email
        sender = c.execute('SELECT * FROM users WHERE id = ?', (sender_id,)).fetchone()

        # Update request status
        c.execute('''
            UPDATE connection_requests
            SET status = 'accepted', updated_at = CURRENT_TIMESTAMP
            WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
        ''', (sender_id, current_user.id))

        # Create connection
        c.execute('''
            INSERT INTO connections (user_id_1, user_id_2)
            VALUES (?, ?)
        ''', (min(sender_id, current_user.id), max(sender_id, current_user.id)))

        conn.commit()

        # Send email to sender about acceptance
        try:
            if sender:
                send_connection_email(
                    sender['email'],
                    sender['name'],
                    current_user.name,
                    current_user.role,
                    'accepted'
                )
        except Exception as e:
            print(f"Email error: {e}")

        conn.close()

        return jsonify({'success': True, 'message': 'Request accepted', 'status': 'connected'}), 200

    except Exception as e:
        print(f"Error accepting connection request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/connection-request/reject/<int:sender_id>', methods=['POST'])
@login_required
def reject_connection_request(sender_id):
    """Reject a connection request"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get sender details for email
        sender = c.execute('SELECT * FROM users WHERE id = ?', (sender_id,)).fetchone()

        # Update request status
        c.execute('''
            UPDATE connection_requests
            SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
            WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
        ''', (sender_id, current_user.id))

        conn.commit()

        # Send email to sender about rejection
        try:
            if sender:
                send_connection_email(
                    sender['email'],
                    sender['name'],
                    current_user.name,
                    current_user.role,
                    'rejected'
                )
        except Exception as e:
            print(f"Email error: {e}")

        conn.close()

        return jsonify({'success': True, 'message': 'Request rejected', 'status': 'none'}), 200

    except Exception as e:
        print(f"Error rejecting connection request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/connection-request/status/<int:user_id>', methods=['GET'])
@login_required
def get_connection_status(user_id):
    """Get connection status between current user and another user"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Check if already connected
        connection = c.execute('''
            SELECT * FROM connections
            WHERE (user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)
        ''', (current_user.id, user_id, user_id, current_user.id)).fetchone()

        if connection:
            conn.close()
            return jsonify({'status': 'connected'}), 200

        # Check if pending request from current user
        sent_request = c.execute('''
            SELECT * FROM connection_requests
            WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
        ''', (current_user.id, user_id)).fetchone()

        if sent_request:
            conn.close()
            return jsonify({'status': 'pending'}), 200

        # Check if pending request to current user
        received_request = c.execute('''
            SELECT * FROM connection_requests
            WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
        ''', (user_id, current_user.id)).fetchone()

        if received_request:
            conn.close()
            return jsonify({'status': 'received', 'sender_id': user_id}), 200

        conn.close()
        return jsonify({'status': 'none'}), 200

    except Exception as e:
        print(f"Error getting connection status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/connection-requests/pending', methods=['GET'])
@login_required
def get_pending_connection_requests():
    """Get all pending connection requests for current user"""
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get pending requests with sender details
        requests = c.execute('''
            SELECT cr.id, cr.sender_id, cr.receiver_id, cr.status, cr.created_at,
                   u.name, u.email, u.role, u.profile_pic
            FROM connection_requests cr
            JOIN users u ON cr.sender_id = u.id
            WHERE cr.receiver_id = ? AND cr.status = 'pending'
            ORDER BY cr.created_at DESC
        ''', (current_user.id,)).fetchall()

        conn.close()

        return jsonify({
            'requests': [dict(req) for req in requests],
            'count': len(requests)
        }), 200

    except Exception as e:
        print(f"Error getting pending requests: {e}")
        return jsonify({'error': str(e)}), 500

# ===== EMAIL HELPER FUNCTION =====

def send_connection_email(recipient_email, recipient_name, sender_name, sender_role, action):
    """
    Send connection-related emails
    Actions: 'request', 'accepted', 'rejected', 'mutual'
    """
    try:
        if action == 'request':
            subject = f'🤝 New Connection Request from {sender_name}'
            html_content = f'''
            <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #f0f4ff 0%, #f8f9ff 100%); padding: 30px; border-radius: 15px;">
                <div style="background: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; border-top: 5px solid #1e3a8a; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                    <h1 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.8rem;">🤝 New Connection Request!</h1>

                    <div style="background: linear-gradient(135deg, rgba(30, 58, 138, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #0ea5e9;">
                        <p style="margin: 0 0 8px 0; color: #0ea5e9; font-weight: 700; font-size: 0.9rem;">📱 ALUMNI HUB NETWORK</p>
                        <p style="margin: 0; color: #1e3a8a; font-size: 1.1rem; font-weight: 800;">Someone wants to connect with you!</p>
                    </div>
                </div>

                <div style="background: white; padding: 25px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #f59e0b; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
                    <h3 style="color: #1e3a8a; margin: 0 0 20px 0; font-size: 1.2rem;">👤 Connection Request Details</h3>

                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a; width: 30%;">From:</td>
                            <td style="padding: 12px 0; color: #333; font-size: 1.1rem; font-weight: 600;">{sender_name}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Role:</td>
                            <td style="padding: 12px 0; color: #333;"><span style="background: #e0e7ff; color: #1e3a8a; padding: 4px 10px; border-radius: 20px; font-size: 0.9rem; font-weight: 600;">{sender_role.upper()}</span></td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Date:</td>
                            <td style="padding: 12px 0; color: #666; font-size: 0.9rem;">{datetime.now().strftime('%d %B %Y at %I:%M %p')}</td>
                        </tr>
                    </table>
                </div>

                <div style="background: linear-gradient(135deg, #1e3a8a 0%, #0ea5e9 100%); padding: 25px; border-radius: 12px; margin-bottom: 15px; color: white; text-align: center;">
                    <p style="margin: 0 0 15px 0; font-size: 1rem; font-weight: 600;">👇 Accept or Reject This Request</p>
                    <p style="margin: 0; font-size: 0.9rem; opacity: 0.95;">Visit your dashboard to manage the request</p>
                </div>

                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                    <p style="margin: 0; color: #666; font-size: 0.85rem;">
                        <strong style="color: #1e3a8a;">Alumni Hub Management System</strong><br>
                        Building Connections, Creating Opportunities<br>
                        © 2026 Alumni Hub. All rights reserved.
                    </p>
                </div>
            </div>
            '''

        elif action == 'accepted':
            subject = f'✓ Your Connection Request to {recipient_name} Was Accepted!'
            html_content = f'''
            <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #f0f4ff 0%, #f8f9ff 100%); padding: 30px; border-radius: 15px;">
                <div style="background: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; border-top: 5px solid #10b981; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                    <h1 style="color: #10b981; margin: 0 0 15px 0; font-size: 1.8rem;">✓ Connection Accepted!</h1>

                    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(10, 150, 105, 0.1) 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #10b981;">
                        <p style="margin: 0 0 8px 0; color: #10b981; font-weight: 700; font-size: 0.9rem;">🎉 GREAT NEWS!</p>
                        <p style="margin: 0; color: #1e3a8a; font-size: 1.1rem; font-weight: 800;">You're now connected!</p>
                    </div>
                </div>

                <div style="background: white; padding: 25px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #10b981;">
                    <h3 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.1rem;">Happy to Connect 🤝</h3>
                    <p style="color: #333; line-height: 1.8; margin: 0;">
                        Great news! <strong>{recipient_name}</strong> (who is a {sender_role}) has accepted your connection request. You are now connected in the Alumni Hub network!
                    </p>
                </div>

                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                    <p style="margin: 0; color: #666; font-size: 0.85rem;">
                        <strong style="color: #1e3a8a;">Alumni Hub Management System</strong><br>
                        Building Connections, Creating Opportunities<br>
                        © 2026 Alumni Hub. All rights reserved.
                    </p>
                </div>
            </div>
            '''

        elif action == 'rejected':
            subject = f'Connection Request Update from {recipient_name}'
            html_content = f'''
            <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #f0f4ff 0%, #f8f9ff 100%); padding: 30px; border-radius: 15px;">
                <div style="background: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; border-top: 5px solid #f59e0b; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                    <h1 style="color: #f59e0b; margin: 0 0 15px 0; font-size: 1.8rem;">📋 Request Update</h1>

                    <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #f59e0b;">
                        <p style="margin: 0 0 8px 0; color: #f59e0b; font-weight: 700; font-size: 0.9rem;">STATUS UPDATE</p>
                        <p style="margin: 0; color: #1e3a8a; font-size: 1.1rem; font-weight: 800;">Your connection request was not accepted</p>
                    </div>
                </div>

                <div style="background: white; padding: 25px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #f59e0b;">
                    <p style="color: #333; line-height: 1.8; margin: 0;">
                        Your connection request to <strong>{recipient_name}</strong> was declined. You can try connecting with other members of the Alumni Hub network!
                    </p>
                </div>

                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                    <p style="margin: 0; color: #666; font-size: 0.85rem;">
                        <strong style="color: #1e3a8a;">Alumni Hub Management System</strong><br>
                        Building Connections, Creating Opportunities<br>
                        © 2026 Alumni Hub. All rights reserved.
                    </p>
                </div>
            </div>
            '''

        elif action == 'mutual':
            subject = f'🎉 You\'re Now Connected with {sender_name}!'
            html_content = f'''
            <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #f0f4ff 0%, #f8f9ff 100%); padding: 30px; border-radius: 15px;">
                <div style="background: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; border-top: 5px solid #10b981; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                    <h1 style="color: #10b981; margin: 0 0 15px 0; font-size: 1.8rem;">🎉 Mutual Connection!</h1>

                    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(10, 150, 105, 0.1) 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #10b981;">
                        <p style="margin: 0 0 8px 0; color: #10b981; font-weight: 700; font-size: 0.9rem;">🌟 INSTANT CONNECTION!</p>
                        <p style="margin: 0; color: #1e3a8a; font-size: 1.1rem; font-weight: 800;">Mutual connection established!</p>
                    </div>
                </div>

                <div style="background: white; padding: 25px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #10b981;">
                    <h3 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.1rem;">Instant Match! 🤝</h3>
                    <p style="color: #333; line-height: 1.8; margin: 0;">
                        You and <strong>{sender_name}</strong> (who is a {sender_role}) have automatically become connected! You both wanted to connect with each other, so the system instantly established your connection.
                    </p>
                </div>

                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                    <p style="margin: 0; color: #666; font-size: 0.85rem;">
                        <strong style="color: #1e3a8a;">Alumni Hub Management System</strong><br>
                        Building Connections, Creating Opportunities<br>
                        © 2026 Alumni Hub. All rights reserved.
                    </p>
                </div>
            </div>
            '''

        else:
            return  # Unknown action

        # Send email
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            html=html_content
        )
        mail.send(msg)

    except Exception as e:
        print(f"Error sending connection email: {e}")
        # Silently fail - don't interrupt request flow if email fails

if __name__ == '__main__':
    init_db()
    app.run(debug=app.config['DEBUG'])
