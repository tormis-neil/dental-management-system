# 🦷 Dental Clinic Management System

A Flask-based web application for managing dental clinic patient records, staff, and operations with role-based access control.

**Academic Demo Project** - Developed for educational purposes

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Default Login Credentials](#default-login-credentials)
- [User Roles & Permissions](#user-roles--permissions)
- [Project Structure](#project-structure)
- [Screenshots](#screenshots)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

### 👥 Patient Management
- Add, edit, view, and delete patient records
- Search patients by name, ID, or phone number
- Filter patients by gender
- Automatic age calculation from date of birth
- Medical information tracking (allergies, conditions, dentist notes)
- Emergency contact information

### 👨‍💼 Staff Management (Manager Only)
- Add and manage staff members
- Activate/deactivate staff accounts
- Password management
- Search and filter staff by status

### 🔐 Security & Access Control
- Role-based access control (Manager, Dentist, Staff, Admin)
- CSRF protection enabled
- Secure password hashing
- Session management with Flask-Login
- Approval workflow for staff deletion requests

### 📊 Audit Logging
- Complete activity tracking
- User action history
- Timestamp for all operations
- Role-based log viewing

### 💾 Backup & Restore
- Database backup creation with timestamps
- Download backup files
- Restore from previous backups
- Manager-only access

---

## 🛠️ Tech Stack

- **Backend:** Flask 3.0.0 (Python)
- **Database:** SQLite3
- **Authentication:** Flask-Login 0.6.3
- **Security:** Flask-WTF 1.2.1 (CSRF Protection)
- **Frontend:** Bootstrap 5.3.0, Bootstrap Icons
- **JavaScript:** Vanilla JS (no jQuery)

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+**
  - **Windows:** Check with `py --version` or `python --version`
  - **Mac/Linux:** Check with `python3 --version`
- **pip** (Python package manager - usually included with Python)
- **Git** (optional, for cloning)

---

## 🚀 Installation

### Step 1: Clone or Download the Project

```bash
# If using Git
git clone <repository-url>
cd dental-management-system

# OR download and extract the ZIP file
```

### Step 2: Install Dependencies

**On Windows (PowerShell/Command Prompt):**
```powershell
# Install required Python packages
py -m pip install -r requirements.txt
```

**On Mac/Linux:**
```bash
# Install required Python packages
pip3 install -r requirements.txt
```

**If you get "pip not found" on Windows:**
```powershell
# Try this instead:
python -m pip install -r requirements.txt

# Or use full path:
C:\Users\YourUsername\AppData\Local\Programs\Python\Python313\python.exe -m pip install -r requirements.txt
```

**Required packages (from requirements.txt):**
```
Flask==3.0.0
Flask-Login==0.6.3
Flask-WTF==1.2.1
Werkzeug==3.0.1
```

### Step 3: Verify Installation

**On Windows:**
```powershell
py -c "import flask; print('Flask installed successfully!')"
```

**On Mac/Linux:**
```bash
python3 -c "import flask; print('Flask installed successfully!')"
```

You should see: `Flask installed successfully!`

---

## ▶️ Running the Application

### Method 1: Direct Python Execution (Recommended)

**On Windows:**
```powershell
# Run the application
py app.py
```

**On Mac/Linux:**
```bash
# Run the application
python3 app.py
```

You should see output like:
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment.
 * Running on http://127.0.0.1:5000
```

### Method 2: Using Flask CLI

**On Windows:**
```powershell
# Set Flask app environment variable
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"

# Run Flask
py -m flask run
```

**On Mac/Linux:**
```bash
# Set Flask app environment variable
export FLASK_APP=app.py
export FLASK_ENV=development

# Run Flask
flask run
```

### Accessing the Application

1. Open your web browser
2. Navigate to: **http://localhost:5000**
3. You'll be redirected to the login page

**That's it! The application is now running! 🎉**

---

## 🔑 Default Login Credentials

The system creates a default manager account on first run:

| Username | Password | Role |
|----------|----------|------|
| `manager` | `12345` | Manager |

**⚠️ IMPORTANT:** Change this password immediately after first login via "My Profile" or "Settings"

### Additional Test Accounts

You may also find these test accounts in the database:

| Username | Password | Role | Access Level |
|----------|----------|------|--------------|
| `STAFF-001` | `staff123` | Staff | Limited (needs approval for deletions) |

*Note: These are automatically created if they exist in your database.*

---

## 👥 User Roles & Permissions

### 🔴 Manager (Full Access)
- ✅ Manage all patients (add/edit/delete)
- ✅ Manage all staff members
- ✅ Approve/deny deletion requests
- ✅ Create and restore database backups
- ✅ View all audit logs
- ✅ Access all system features

### 🟡 Dentist (High Access)
- ✅ Manage patients (add/edit/delete directly)
- ✅ View patient medical information
- ✅ Add dentist notes and medical details
- ✅ View audit logs
- ❌ Cannot manage staff
- ❌ Cannot access backups

### 🟢 Staff (Limited Access)
- ✅ Add new patients
- ✅ Edit basic patient information
- ✅ View patient records
- ✅ Request patient deletion (requires manager approval)
- ❌ Cannot delete patients directly
- ❌ Cannot view/edit medical information
- ❌ Cannot access staff management
- ❌ View only own audit logs

### 🔵 Admin (Full Access)
- Same as Manager with administrative privileges

---

## 📁 Project Structure

```
dental-management-system/
│
├── app.py                  # Main Flask application (routes & logic)
├── models.py               # Database models & schema
├── config.py               # Application configuration
├── utils.py                # Helper functions (decorators, backups)
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
│
├── dental_clinic.db       # SQLite database (auto-generated)
│
├── templates/             # HTML templates (Jinja2)
│   ├── base.html          # Base template with navbar
│   ├── login.html         # Login page
│   ├── dashboard.html     # Main dashboard
│   ├── patients.html      # Patient list view
│   ├── add_patient.html   # Add patient form
│   ├── edit_patient.html  # Edit patient form
│   ├── view_patient.html  # Patient details
│   ├── staff.html         # Staff list (manager only)
│   ├── add_staff.html     # Add staff form
│   ├── edit_staff.html    # Edit staff form
│   ├── my_profile.html    # User profile page
│   ├── settings.html      # User settings
│   ├── audit_logs.html    # Activity logs
│   ├── backup.html        # Backup management
│   └── pending_requests.html  # Deletion requests
│
└── static/                # Static assets
    ├── css/
    │   └── style.css      # Custom styles
    ├── js/
    │   └── script.js      # JavaScript functionality
    └── images/
        ├── dental_logo.png
        └── dental_logo_dashboard.png
```

---

## 🎨 Screenshots

### Login Page
Beautiful split-screen design with animated logo
- Secure authentication
- CSRF protection
- Password visibility toggle

### Dashboard
- Role-based statistics cards
- Recent activities widget
- Recent patients list
- Pending requests (managers only)

### Patient Management
- Comprehensive search and filter
- Sortable patient list
- Detailed patient profiles
- Medical information tracking

---

## 🔧 Troubleshooting

### Issue: "pip is not recognized" (Windows)

**Solution:**
```powershell
# Use py launcher instead:
py -m pip install -r requirements.txt

# Or ensure pip:
py -m ensurepip --upgrade
```

### Issue: "Module not found" error

**Solution (Windows):**
```powershell
# Reinstall dependencies
py -m pip install -r requirements.txt
```

**Solution (Mac/Linux):**
```bash
# Reinstall dependencies
pip3 install -r requirements.txt
```

### Issue: "Address already in use"

**Solution (Windows):**
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or restart your computer
```

**Solution (Mac/Linux):**
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use a different port
python3 app.py --port 5001
```

### Issue: Database errors

**Solution (Windows):**
```powershell
# Delete and recreate database
del dental_clinic.db
py app.py  # Database will be recreated automatically
```

**Solution (Mac/Linux):**
```bash
# Delete and recreate database
rm dental_clinic.db
python3 app.py  # Database will be recreated automatically
```

### Issue: Can't log in

**Solution:**
- Ensure you're using the default credentials: `manager` / `12345`
- Check if database exists: `ls -la dental_clinic.db`
- Try deleting the database to reset

### Issue: CSRF token missing

**Solution:**
- Clear your browser cookies
- Restart the application
- Ensure you're using the login form, not direct URL access

### Issue: Static files not loading (CSS/JS)

**Solution:**
- Verify `static/` folder exists
- Check browser console for 404 errors
- Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
- Ensure Flask is running from the project root directory

---

## 📚 How to Use

### 1. First Login
1. Start the application: `python3 app.py`
2. Open browser: http://localhost:5000
3. Login with: `manager` / `12345`
4. Change password in "My Profile"

### 2. Adding Patients
1. Click "Patients" in navigation
2. Click "Add New Patient" button
3. Fill in required fields (First Name, Last Name)
4. Managers/Dentists can add medical information
5. Click "Add Patient"

### 3. Managing Staff (Managers Only)
1. Click "Staff" in navigation
2. Click "Add New Staff" button
3. Enter username, password, full name, email
4. Staff member can now log in
5. Edit or deactivate staff as needed

### 4. Approval Workflow (Staff → Manager)
1. **Staff:** Request deletion from patient list
2. **Manager:** View "Pending Requests" on dashboard
3. **Manager:** Approve or deny the request
4. Patient is deleted only after approval

### 5. Database Backup
1. Login as Manager
2. Click "Backup" in navigation
3. Click "Create New Backup"
4. Download or restore backups as needed

---

## 🔒 Security Notes

**For Academic Demo:**
- ✅ CSRF protection enabled
- ✅ Password hashing implemented
- ✅ Role-based access control
- ✅ SQL injection prevention (parameterized queries)
- ✅ Session management

**⚠️ Not Production-Ready:**
- Default credentials are weak
- Debug mode is enabled
- No rate limiting
- No HTTPS enforcement
- No session timeout configured

**For production use, see `QA_TESTING_REPORT.md` for comprehensive security recommendations.**

---

## 🧪 Testing

See `MANUAL_TESTING.md` for comprehensive manual testing guide including:
- Feature testing checklist
- Role-based access testing
- Security testing
- Bug reporting template

---

## 📝 Database Schema

The application uses SQLite with 4 main tables:

### Users Table
- id, username, password_hash, full_name, email
- role (manager/staff/dentist/admin)
- is_active, created_at

### Patients Table
- id, first_name, last_name, date_of_birth, gender
- phone, email, address
- emergency_contact_name, emergency_contact_phone
- allergies, existing_condition, dentist_notes
- assigned_dentist, created_by, created_at, updated_at

### Audit Logs Table
- id, user_id, username, action_type, details, timestamp

### Pending Requests Table
- id, patient_id, requested_by, status
- requested_at, approved_by, approved_at

---

## 🎓 Academic Project Information

**Project Type:** Dental Clinic Management System
**Purpose:** Academic Demonstration
**Framework:** Flask (Python Web Framework)
**Database:** SQLite3
**Authentication:** Flask-Login with role-based access control

**Key Learning Concepts:**
- MVC architecture in Flask
- Database design and ORM
- User authentication & authorization
- CSRF protection
- Form handling and validation
- Jinja2 templating
- Bootstrap frontend integration
- RESTful routing

---

## 🐛 Known Limitations

1. **SQLite Concurrency:** Not suitable for many concurrent users (fine for demo)
2. **No Email Functionality:** No password reset or email notifications
3. **Basic Search:** Simple text-based search (no fuzzy matching)
4. **No Export:** Cannot export data to PDF/Excel
5. **No Appointments:** No scheduling or calendar functionality

These are intentional limitations for an academic demo project.

---

## 🆘 Getting Help

If you encounter issues:

1. **Check Troubleshooting section above**
2. **Review `MANUAL_TESTING.md`** for testing guidance
3. **Check `QA_TESTING_REPORT.md`** for detailed system analysis
4. **Verify Python version:** `python3 --version` (requires 3.11+)
5. **Check if port 5000 is available**

---

## 📄 License

This is an academic project for educational purposes only.

---

## ✅ Quick Start Checklist

- [ ] Python 3.11+ installed
- [ ] Dependencies installed (`pip3 install -r requirements.txt`)
- [ ] Application runs (`python3 app.py`)
- [ ] Browser opens http://localhost:5000
- [ ] Can login with `manager` / `12345`
- [ ] Dashboard displays correctly
- [ ] Can add a test patient
- [ ] Can view audit logs

**If all checked, you're ready to demo! 🎉**

---

## 🎯 Demo Presentation Tips

1. **Start with login** - Show role-based access
2. **Show dashboard** - Highlight statistics and recent activity
3. **Add a patient** - Demonstrate form validation
4. **Show staff workflow** - Staff requests deletion, manager approves
5. **Create backup** - Show backup/restore functionality
6. **View audit logs** - Show activity tracking
7. **Show responsive design** - Resize browser window

---

**Built with ❤️ for academic learning**

*Last Updated: November 2025*
