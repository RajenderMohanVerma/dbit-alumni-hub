from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from config import config

app = Flask(__name__)
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

DB_NAME = app.config['DB_NAME']

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
        # Avatar generation logic
        avatar = user['profile_pic'] if user['profile_pic'] else f"https://ui-avatars.com/api/?name={user['name']}&background=0D6EFD&color=fff"
        return User(user['id'], user['name'], user['email'], user['role'], avatar)
    return None

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Complex Table with LPU/Vaave fields
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            role TEXT NOT NULL,      -- student, alumni, admin, faculty
            department TEXT,         -- LPU Field
            degree TEXT,             -- LPU Field
            pass_year INTEGER,       -- LPU Field
            reg_number TEXT,         -- LPU Field
            company TEXT,            -- Alumni Field
            designation TEXT,        -- Alumni Field
            profile_pic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Admin if not exists
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

            # You can add email sending logic here
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
            # Role based redirect
            if user['role'] == 'admin': return redirect(url_for('dashboard_admin'))
            if user['role'] == 'alumni': return redirect(url_for('dashboard_alumni'))
            return redirect(url_for('dashboard_student'))
        else:
            flash('Invalid Email or Password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Collecting Data (using .get() for optional fields)
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

            # Validation
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

# --- DASHBOARDS ---

@app.route('/student/dashboard')
@login_required
def dashboard_student():
    conn = get_db_connection()
    # Fetch all alumni
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
    if current_user.role != 'admin': return redirect(url_for('home'))
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    
    # Chart Data Preparation
    a_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='alumni'").fetchone()[0]
    s_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
    
    # Dummy Chart Data (Years vs Placements)
    chart_data = {
        'years': ['2021', '2022', '2023', '2024', '2025'],
        'placements': [120, 150, 200, 250, 310],
        'funds': [5, 12, 15, 25, 40]
    }
    conn.close()
    return render_template('dashboard_admin.html', users=users, a_count=a_count, s_count=s_count, chart_data=chart_data)

# Import the social routes blueprint
from routes.social_routes import social_bp

# Register blueprints
app.register_blueprint(social_bp)

if __name__ == '__main__':
    init_db()
    app.run(debug=app.config['DEBUG'])