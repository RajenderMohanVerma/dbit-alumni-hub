from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

DB_NAME = "/tmp/college_pro.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

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
        avatar = user['profile_pic'] if user['profile_pic'] else f"https://ui-avatars.com/api/?name={user['name']}&background=0D6EFD&color=fff"
        return User(user['id'], user['name'], user['email'], user['role'], avatar)
    return None

# --- DATABASE SETUP ---
def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT,
                role TEXT NOT NULL,
                department TEXT,
                degree TEXT,
                pass_year INTEGER,
                reg_number TEXT,
                company TEXT,
                designation TEXT,
                profile_pic TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute("SELECT * FROM users WHERE role='admin'")
        if not c.fetchone():
            pw = generate_password_hash("admin123")
            c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                      ("Super Admin", "admin@college.edu", pw, "admin"))
        
        conn.commit()
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
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
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
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '')
            password = generate_password_hash(request.form.get('password', ''))
            role = request.form.get('role', 'student')
            dept = request.form.get('department', '')
            degree = request.form.get('degree', '')
            pass_year = request.form.get('pass_year', '')
            reg_num = request.form.get('reg_number', '')
            company = request.form.get('company', '')
            designation = request.form.get('designation', '')

            if not name or not email or not request.form.get('password'):
                flash('Name, Email, and Password are required!', 'warning')
                return render_template('register.html')

            conn = get_db_connection()
            conn.execute('''INSERT INTO users 
                (name, email, password, phone, role, department, degree, pass_year, reg_number, company, designation) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (name, email, password, phone, role, dept, degree, pass_year, reg_num, company, designation))
            conn.commit()
            conn.close()
            flash('Registration Successful! Please Login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered!', 'warning')
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/student/dashboard')
@login_required
def dashboard_student():
    conn = get_db_connection()
    alumni = conn.execute("SELECT * FROM users WHERE role='alumni'").fetchall()
    conn.close()
    return render_template('dashboard_student.html', alumni=alumni)

@app.route('/alumni/dashboard')
@login_required
def dashboard_alumni():
    return render_template('dashboard_alumni.html')

@app.route('/admin/dashboard')
@login_required
def dashboard_admin():
    if current_user.role != 'admin': 
        return redirect(url_for('home'))
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    
    a_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='alumni'").fetchone()[0]
    s_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
    
    chart_data = {
        'years': ['2021', '2022', '2023', '2024', '2025'],
        'placements': [120, 150, 200, 250, 310],
        'funds': [5, 12, 15, 25, 40]
    }
    conn.close()
    return render_template('dashboard_admin.html', users=users, a_count=a_count, s_count=s_count, chart_data=chart_data)

try:
    from routes.social_routes import social_bp
    app.register_blueprint(social_bp)
except ImportError:
    pass

init_db()
