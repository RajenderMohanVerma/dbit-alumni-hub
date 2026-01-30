# Alumni App

A Flask-based Alumni Management System for colleges.

## Deployment on Vercel

### Step 1: GitHub Push

```bash
git add .
git commit -m "Setup for Vercel deployment"
git push origin main
```

### Step 2: Vercel Deployment

1. Go to https://vercel.com
2. Sign up with GitHub
3. Click **New Project**
4. Select your **Alumni-App** repository
5. Configure environment variables:
   - `SECRET_KEY`: Your secure key (min 32 chars)
   - `FLASK_ENV`: production
6. Click **Deploy**

### Step 3: Add Environment Variables

1. Go to Project Settings → Environment Variables
2. Add:
   - `SECRET_KEY` = your-secure-key-here
   - `FLASK_ENV` = production

## Local Development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python api/app.py
```

## Default Credentials

- Email: admin@college.edu
- Password: admin123

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
