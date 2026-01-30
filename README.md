# Alumni App 🎓

A comprehensive Flask-based Alumni Management System for educational institutions. Connect students, alumni, and faculty in one unified platform.

## 🌟 Features

### Multi-Role System

- **Students**: View alumni network, explore career opportunities
- **Alumni**: Manage profiles, register for events, mentor students
- **Faculty**: Share expertise, manage office hours, guide students
- **Admin**: Manage all users, view statistics, monitor activities

### Core Features

- ✅ **Interactive Alumni Dashboard** - Search, filter, and connect with alumni
- ✅ **Alumni Meet Registration** - Complete event management system
- ✅ **Role-Based Dashboards** - Customized experience for each role
- ✅ **Profile Management** - Edit profiles, upload achievements
- ✅ **Student to Alumni Upgrade** - Seamless transition after graduation
- ✅ **Admin Panel** - User management and analytics
- ✅ **WAL Database** - Optimized SQLite with concurrent access

## 🛠️ Tech Stack

- **Backend**: Flask 2.3.2
- **Database**: SQLite with WAL mode
- **Authentication**: Flask-Login
- **Security**: Werkzeug (password hashing)
- **Frontend**: Bootstrap 5, Jinja2
- **Deployment**: Vercel, Heroku

## 📋 Prerequisites

- Python 3.7+
- pip (Python package manager)
- Git

## 🚀 Quick Start

### Local Development

```bash
# 1. Clone the repository
git clone <repository-url>
cd "Alumni App"

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file
echo SECRET_KEY=your-secret-key-here > .env

# 6. Run the application
python app.py
```

Visit `http://localhost:5000` in your browser.

## 📝 Default Credentials

- **Email**: admin@college.edu
- **Password**: admin123

## Project Structure

```
Alumni App/
├── api/
│   └── app.py
├── templates/
├── static/
├── vercel.json
├── requirements.txt
├── README.md
└── .gitignore
```
